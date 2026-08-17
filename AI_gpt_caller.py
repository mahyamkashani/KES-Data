import os

from openai import OpenAI

MODEL = os.environ.get("KES_GPT_MODEL", "gpt-4o-mini")

_client = None


def _load_key():
    
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if key:
        return key

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                if name.strip() in ("OPENAI_API_KEY", "OPENAI_KEY"):
                    return value.strip().strip("'\"")
    raise RuntimeError(
        "No API key found. Set OPENAI_API_KEY, or put OPENAI_KEY=... in a .env "
        "file next to this module."
    )


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=_load_key())
    return _client


def get_gpt_response(prompt):
    """Send a prompt to the chat model and return the response message.

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
