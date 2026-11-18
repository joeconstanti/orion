"""Split cumulative model text without classifying ordinary prose as reasoning."""
import re


_CLOSING_TAG = '</think>'
_CLOSING_TAG_PATTERN = re.compile(_CLOSING_TAG, re.IGNORECASE | re.ASCII)


def split_output(text: str, final: bool = False) -> tuple[str, str]:
    opening = '<think>'
    if not final and opening.startswith(text.lower()):
        return '', ''
    if not text.lower().startswith(opening):
        return '', text
    body = text[len(opening):]
    match = _CLOSING_TAG_PATTERN.search(body)
    if match:
        return body[:match.start()], body[match.end():]
    if not final:
        for size in range(min(len(body), len(_CLOSING_TAG) - 1), 0, -1):
            if _CLOSING_TAG.startswith(body[-size:].lower()):
                return body[:-size], ''
    return body, ''
