"""Split cumulative model text without classifying ordinary prose as reasoning."""
def split_output(text: str, final: bool = False) -> tuple[str, str]:
    opening, closing = '<think>', '</think>'
    if not final and opening.startswith(text.lower()):
        return '', ''
    if not text.lower().startswith(opening):
        return '', text
    body = text[len(opening):]
    end = body.lower().find(closing)
    if end >= 0:
        return body[:end], body[end + len(closing):]
    if not final:
        for size in range(min(len(body), len(closing) - 1), 0, -1):
            if closing.startswith(body[-size:].lower()):
                return body[:-size], ''
    return body, ''
