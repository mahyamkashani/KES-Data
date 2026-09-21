"""
Usage:  python populate_ontology.py [axioms.json] [--source=tbox.rdf] [--target=out.rdf]
"""
import json
import os
import re
import sys
import Validator_axiom_semantics
import ontology_importer
import Creator_ontology_Individual_Creator as IndividualCreator
import Creator_ontology_Property_Creator as PropertyCreator
from owlready2 import onto_path

KES = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KES)
HERE = os.path.dirname(os.path.abspath(__file__))

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
_opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
SOURCE = os.path.abspath(_opts.get(
    "source", os.path.join(HERE, "Ontology", "new", "marine_report.rdf")))
_DEFAULT_DOC = "AL374 CR ifm-geomar_rep51-1"#"ifm-geomar_rep10"
AXIOMS = _args if _args else [
    os.path.join(HERE, "outputs", "", f"output_{pattern}_{_DEFAULT_DOC}.json")
    for pattern in ("binary", "subclass", "attributes", "nary")
]


def document_stem(paths):
    """
    output_<pattern>_<document>.json,
    """
    stems = []
    for path in paths:
        stem = re.sub(r"^output_[A-Za-z]+_", "",
                      os.path.splitext(os.path.basename(path))[0])
        if stem not in stems:
            stems.append(stem)
    #mixing reports in one run is unusual but should still name itself honestly
    return "__".join(stems) if stems else "axioms"


TARGET = os.path.abspath(_opts.get("target", os.path.join(
    HERE, f"marine_survey_populated_{document_stem(AXIOMS)}.rdf")))

EXCLUDE = set()

ALIAS = {
    "Mission_AL533": "AL533",
}

PROPERTY_ALIAS = {
    "island name": "locationName",
    "islandName": "locationName",
}


VALUE_ALIAS = {
    "hasStatus": {
        "completed": "SUCCESSFUL",
        "success": "SUCCESSFUL",
        "partially successful": "PartialSUCCESSFUL",
        "partial": "PartialSUCCESSFUL",
        "failure": "FAILED",
    },
}


def sanitise(name):
    """owlready2 resolves individuals via getattr, so names need to be identifiers."""
    clean = re.sub(r"\W+", "_", name.strip()).strip("_")
    return ALIAS.get(clean, clean)


def named_class(onto, constraints):

    if not constraints:
        return None
    name = getattr(constraints[0], "name", None)
    if name is None or getattr(onto, name, None) is None:
        return None
    return name


def enumerated_values(prop):
    """The closed value list of a data property, or None if its range is open."""
    from owlready2 import OneOf
    for constraint in getattr(prop, "range", None) or []:
        if isinstance(constraint, OneOf):
            return list(constraint.instances)
    return None


def fit_to_range(prop_name, prop, value):
    members = enumerated_values(prop)
    if members is None or value in members:
        return value, None
    key = str(value).strip().lower()
    #a plain case difference needs no table entry
    match = VALUE_ALIAS.get(prop_name, {}).get(key) or next(
        (m for m in members if m.lower() == key), None)
    if match is None:
        return None, f"{value!r} is outside the {prop_name} enumeration {members}"
    return match, None


def main():
    axioms, individuals, nary = [], {}, []
    for path in ([AXIOMS] if isinstance(AXIOMS, str) else AXIOMS):
        with open(path) as fh:
            payload = json.load(fh)
        if "ObjectPropertyAxiom" in payload:
            axioms.extend(payload["ObjectPropertyAxiom"])
        elif "Individuals" in payload:
            individuals.update(payload["Individuals"])
        elif "NaryPropertyAxiom" in payload:
            for block in payload["NaryPropertyAxiom"].values():
                nary.extend(block.get("Axioms", []))
        else:
             for subclasses in payload.values():
                if not isinstance(subclasses, dict):
                    raise ValueError(f"{path}: unrecognised shape, got {sorted(payload)}")
                for subclass, rows in subclasses.items():
                    for row in rows:
                        name = row.get("individual_name")
                        if not name:
                            continue
                        fields = {k: v for k, v in row.items() if k != "individual_name"}
                        individuals[name] = dict(fields, **{"class": subclass})

    for d in (os.path.dirname(SOURCE), HERE, KES):
        if d and d not in onto_path:
            onto_path.append(d)

    onto = ontology_importer.ontology_reader("file://" + SOURCE)
    before = len(list(onto.individuals()))

    created, asserted, skipped = [], [], []

    for axiom in axioms:
        subject_raw, object_raw = axiom["INDIVIDUAL"]
        prop = axiom["OBJECT_PROPERTY"]

        if f"{subject_raw} {prop} {object_raw}" in EXCLUDE:
            skipped.append(axiom["AXIOM"])
            continue

        subject, object_ = sanitise(subject_raw), sanitise(object_raw)
        labels = {}
        if subject == axiom["DOMAIN"] and object_ == axiom["RANGE"]:
            skipped.append(axiom["AXIOM"] + "   [class name in both individual slots]")
            continue
        if object_ == axiom["RANGE"]:
            minted = f"{subject}_{object_}"
            labels[minted] = object_raw
            object_ = minted
        elif subject == axiom["DOMAIN"]:
            minted = f"{object_}_{subject}"
            labels[minted] = subject_raw
            subject = minted

        pairs = ((subject, axiom["DOMAIN"]), (object_, axiom["RANGE"]))

        missing = [c for _, c in pairs if getattr(onto, c, None) is None]
        if missing:
            skipped.append(axiom["AXIOM"] + f"   [class {', '.join(missing)} not in ontology]")
            continue
        if getattr(onto, prop, None) is None:
            skipped.append(axiom["AXIOM"] + f"   [object property {prop!r} not in ontology]")
            continue

        for individual_name, class_name in pairs:
            # Re-running must not duplicate individuals already asserted.
            if getattr(onto, individual_name, None) is None:
                IndividualCreator.createIndividual(onto, class_name, individual_name)
                #a minted name is ours, not the report's; keep what the report
                #actually called the device so the label still reads "USBL"
                if individual_name in labels:
                    getattr(onto, individual_name).label = [labels[individual_name]]
                created.append(f"{individual_name} : {class_name}"
                               + (f"   [named by type: {labels[individual_name]!r}]"
                                  if individual_name in labels else ""))

        PropertyCreator.createObjPropertyForIndividual(onto, prop, subject, object_)
        asserted.append(f"{subject} {prop} {object_}")

    for line in nary:
        parts = line.split()
        if len(parts) != 3:
            skipped.append(f"{line}   [not a subject/property/object triple]")
            continue
        subject_raw, prop, object_raw = parts
        relation = getattr(onto, prop, None)
        if relation is None:
            skipped.append(f"{line}   [object property {prop!r} not in ontology]")
            continue

        pairs = ((sanitise(subject_raw), named_class(onto, relation.domain)),
                 (sanitise(object_raw), named_class(onto, relation.range)))
        if any(class_name is None for _, class_name in pairs):
            skipped.append(f"{line}   [{prop} has no single named domain/range to type from]")
            continue

        for individual_name, class_name in pairs:
            if getattr(onto, individual_name, None) is None:
                IndividualCreator.createIndividual(onto, class_name, individual_name)
                created.append(f"{individual_name} : {class_name}")

        PropertyCreator.createObjPropertyForIndividual(
            onto, prop, sanitise(subject_raw), sanitise(object_raw)
        )
        asserted.append(line)

    for raw_name, fields in individuals.items():
        class_name = fields.get("class")
        name = sanitise(raw_name)
        if getattr(onto, class_name, None) is None:
            skipped.append(f"{raw_name} : {class_name}   [class not in ontology]")
            continue
        if name == class_name:
            skipped.append(f"{raw_name} : {class_name}   [class name in individual slot]")
            continue
        if getattr(onto, name, None) is None:
            IndividualCreator.createIndividual(onto, class_name, name)
            created.append(f"{name} : {class_name}")
        for raw_prop, value in fields.items():
            if raw_prop == "class" or value in (None, ""):
                continue
            prop = PROPERTY_ALIAS.get(raw_prop, raw_prop)
            if getattr(onto, prop, None) is None:
                skipped.append(f"{raw_name} {raw_prop}={value!r}   [data property not in ontology]")
                continue

            value, outside = fit_to_range(prop, getattr(onto, prop), value)
            if outside:
                skipped.append(f"{raw_name} {raw_prop}   [{outside}]")
                continue
            try:
                PropertyCreator.createDataPropertyForIndividual(onto, prop, name, value)
                asserted.append(f"{name} {prop} {value}")
                continue
            except (ValueError, TypeError) as exc:
                #a numeric property handed "50-310 meters" cannot take it, but the
                #T-box pairs each such property with a <prop>Text companion that
                #keeps the report's own wording rather than dropping the fact.
                fallback = f"{prop}Text"
                if getattr(onto, fallback, None) is None:
                    skipped.append(f"{raw_name} {raw_prop}={value!r}   [{exc}]")
                    continue
            try:
                PropertyCreator.createDataPropertyForIndividual(onto, fallback, name, value)
                asserted.append(f"{name} {fallback} {value}   [{prop} could not take it]")
            except (ValueError, TypeError) as exc:
                skipped.append(f"{raw_name} {prop}={value!r}   [{exc}]")

    onto.save(file=TARGET, format="rdfxml")

    consistent, verdict = Validator_axiom_semantics.check_consistency(TARGET)
    print(f"\n{verdict}")

    print(f"individuals before: {before}  after: {len(list(onto.individuals()))}")
    print(f"\ncreated {len(created)} individuals:")
    for entry in created:
        print(f"  + {entry}")
    print(f"\nasserted {len(asserted)} axioms:")
    for entry in asserted:
        print(f"  + {entry}")
    if skipped:
        print(f"\nskipped {len(skipped)} excluded axioms:")
        for entry in skipped:
            print(f"  - {entry}")
    print(f"\nwritten to {TARGET}")


if __name__ == "__main__":
    main()
