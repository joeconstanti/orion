"""Validate settings and replace local files atomically with private permissions."""
import json
import os
from pathlib import Path
import tempfile


def write_settings(settings: dict, filename: str):
    if not isinstance(settings, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in settings.items()):
        raise ValueError("Settings must contain string values")
    target = Path(filename)
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=".orion-settings-", suffix=".tmp", dir=target.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def read_settings(filename: str, defaults: dict) -> dict:
    target = Path(filename)
    if not target.exists():
        return dict(defaults)
    with target.open(encoding="utf-8") as handle:
        saved = json.load(handle)
    if not isinstance(saved, dict):
        raise ValueError("Settings must be an object")
    result = dict(defaults)
    for key in defaults:
        if key in saved:
            if not isinstance(saved[key], str):
                raise ValueError("Setting values must be strings")
            result[key] = saved[key]
    return result
