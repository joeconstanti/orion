"""Bounded, read-only checks for Orion service configuration."""
from urllib.parse import urlsplit
import httpx


def validate_service_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Use an HTTP(S) URL without credentials, query, or fragment")
    try:
        parsed.port
    except ValueError:
        raise ValueError("Invalid service port") from None
    return url.rstrip("/")


def ollama_models(url: str, *, transport=None) -> list[str]:
    url = validate_service_url(url)
    with httpx.Client(timeout=5, follow_redirects=False, transport=transport) as client:
        response = client.get(f"{url}/api/tags")
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        raise ValueError("Unexpected model list")
    return [entry["name"] for entry in data["models"]
            if isinstance(entry, dict) and isinstance(entry.get("name"), str) and entry["name"]]
