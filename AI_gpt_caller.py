import os

from openai import OpenAI

MODEL = os.environ.get("KES_GPT_MODEL", "gpt-4o-mini")

_client = None


def _load_key():
    
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if key:
        return key

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    commented = False
    if not os.path.exists(env_path):
        detail = "there is no .env file at %s" % env_path
    else:
        with open(env_path) as fh:
            for line in fh:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                name, _, value = line.lstrip("#").partition("=")
                if name.strip() not in ("OPENAI_API_KEY", "OPENAI_KEY"):
                    continue
                if line.startswith("#"):
                    #the usual cause: the key line is still commented out
                    commented = True
                    continue
                value = value.strip().strip("'\"")
                if value:
                    return value
        if commented:
            detail = "every key line in %s is commented out" % env_path
        else:
            detail = "%s has no OPENAI_API_KEY line with a value" % env_path
    raise RuntimeError(
        "No API key found: %s. Set OPENAI_API_KEY, or put OPENAI_KEY=... in a "
        ".env file next to this module." % detail
    )


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=_load_key())
    return _client


def get_gpt_response(prompt):
    """
    The returned object exposes `.content`, which is what the
    Extractor_* modules read.
    """
    completion = _get_client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": "You are an ontology engineering assistant. Answer with JSON only."},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message
