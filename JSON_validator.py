import json
import re

def validate_json(content):
    if content is None:
        raise ValueError("LLM returned no content")

    fenced = re.match(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", content, re.DOTALL)
    if fenced:
        content = fenced.group(1)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"No JSON object found in LLM reply: {content[:200]!r}")
    try:
        return json.loads(content[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in LLM reply: {exc}") from exc
