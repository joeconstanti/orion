"""Validate the complete bundled catalog without executing skill resources."""
from pathlib import Path
import json
from skills import SkillRegistry


def main():
    root = Path(__file__).resolve().parents[1] / '.agents' / 'skills'
    registry = SkillRegistry(root)
    expected = {folder.name for folder in root.iterdir() if folder.is_dir()}
    missing = sorted(expected - registry.skills.keys())
    print(json.dumps({'skills': sorted(registry.skills), 'diagnostics': registry.diagnostics, 'missing': missing}))
    return int(bool(registry.diagnostics or missing or not registry.skills))


if __name__ == '__main__':
    raise SystemExit(main())
