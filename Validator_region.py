"""Region check for extracted coordinates.

OWL cannot compare one individual's latitude against another individual's
bounding box -- that is variable comparison plus arithmetic, outside the logic.
So the bounding boxes live on TerrainArea individuals in the ontology and the
comparison is done here in SPARQL.

    python Validator_region.py output_attributes_<doc>.json

Reports, for every extracted individual carrying coordinates, which terrain
area it falls inside -- and flags the ones that fall inside none.
"""
import json
import re
import sys

from rdflib import Graph

ONTOLOGY = "marine_survey.rdf"

BBOX_QUERY = """
PREFIX : <http://oru.se/marinellm/survey#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?area ?label ?minLat ?maxLat ?minLon ?maxLon
WHERE {
    ?area a :TerrainArea ;
          :minLatitude  ?minLat ;
          :maxLatitude  ?maxLat ;
          :minLongitude ?minLon ;
          :maxLongitude ?maxLon .
    OPTIONAL { ?area rdfs:label ?label }
}
"""

# 38.4983  |  38°29.90'  |  38 29.90 N  |  38°29'54"N  |  -38.5
COORD = re.compile(
    r"""^\s*(?P<sign>[-+])?\s*
        (?P<deg>\d+(?:\.\d+)?)\s*[°d ]?\s*
        (?:(?P<min>\d+(?:\.\d+)?)\s*['m ]?\s*)?
        (?:(?P<sec>\d+(?:\.\d+)?)\s*["s]?\s*)?
        (?P<hemi>[NSEWnsew])?\s*$""",
    re.VERBOSE,
)


def to_decimal_degrees(value):
    """Normalise a coordinate to signed decimal degrees, or None if unparseable."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("′", "'").replace("″", '"').replace("°", "°")
    m = COORD.match(text)
    if not m:
        return None
    deg = float(m.group("deg"))
    deg += float(m.group("min") or 0) / 60.0
    deg += float(m.group("sec") or 0) / 3600.0
    if m.group("sign") == "-" or (m.group("hemi") or "").upper() in ("S", "W"):
        deg = -deg
    return deg


def load_boxes(path=ONTOLOGY):
    g = Graph()
    g.parse(path)
    boxes = []
    for row in g.query(BBOX_QUERY):
        boxes.append({
            "name": str(row.label or row.area).rsplit("#", 1)[-1],
            "minLat": float(row.minLat), "maxLat": float(row.maxLat),
            "minLon": float(row.minLon), "maxLon": float(row.maxLon),
        })
    return boxes


def regions_containing(lat, lon, boxes):
    return [b["name"] for b in boxes
            if b["minLat"] <= lat <= b["maxLat"] and b["minLon"] <= lon <= b["maxLon"]]


def iter_individuals(data):
    """Yield (name, properties) for the shapes the extractors produce."""
    if isinstance(data, dict) and isinstance(data.get("Individuals"), dict):
        yield from data["Individuals"].items()
    elif isinstance(data, dict):
        for parent in data.values():
            if isinstance(parent, dict):
                for rows in parent.values():
                    if isinstance(rows, list):
                        for row in rows:
                            if isinstance(row, dict):
                                yield row.get("individual_name", "?"), row


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)

    boxes = load_boxes()
    if not boxes:
        raise SystemExit(f"no TerrainArea bounding boxes found in {ONTOLOGY}")
    print(f"{len(boxes)} region(s) from {ONTOLOGY}:")
    for b in boxes:
        print(f"  {b['name']:20} lat {b['minLat']}..{b['maxLat']}  lon {b['minLon']}..{b['maxLon']}")

    with open(sys.argv[1]) as fh:
        data = json.load(fh)

    checked = problems = 0
    print(f"\n{'individual':24} {'latitude':>12} {'longitude':>12}  verdict")
    for name, props in iter_individuals(data):
        if not isinstance(props, dict):
            continue
        raw_lat = props.get("latitude")
        raw_lon = props.get("longitude")
        if raw_lat is None and raw_lon is None:
            continue
        checked += 1
        lat, lon = to_decimal_degrees(raw_lat), to_decimal_degrees(raw_lon)
        if lat is None or lon is None:
            verdict = f"UNPARSEABLE ({raw_lat!r}, {raw_lon!r})"
            problems += 1
        else:
            hits = regions_containing(lat, lon, boxes)
            if hits:
                verdict = "ok -> " + ", ".join(hits)
            else:
                verdict = "OUT OF EVERY REGION"
                problems += 1
        shown_lat = f"{lat:.4f}" if lat is not None else str(raw_lat)[:12]
        shown_lon = f"{lon:.4f}" if lon is not None else str(raw_lon)[:12]
        print(f"  {name[:22]:24} {shown_lat:>12} {shown_lon:>12}  {verdict}")

    print(f"\nchecked {checked} individual(s) with coordinates, {problems} problem(s)")
    if checked == 0:
        print("note: the extraction produced no latitude/longitude values at all")
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
