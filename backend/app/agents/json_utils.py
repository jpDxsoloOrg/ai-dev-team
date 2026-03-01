import json
import re


def extract_json_object(text: str) -> str | None:
    """Extract the first balanced JSON object from text using brace matching."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def extract_json_array(text: str) -> str | None:
    """Extract the first balanced JSON array from text using bracket matching."""
    start = text.find("[")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_json_response(response: str, expect_array: bool = False) -> dict | list | None:
    """Parse JSON from an LLM response, handling markdown fences and extra text."""
    # Try extracting from code fences first
    fence_pattern = r"```(?:json)?\s*([\[\{].*?[\]\}])\s*```"
    fence_match = re.search(fence_pattern, response, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try brace/bracket matching
    extractor = extract_json_array if expect_array else extract_json_object
    extracted = extractor(response)
    if extracted:
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass

    # Strip fences and try whole response
    cleaned = re.sub(r"```(?:json)?|```", "", response).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
