"""Run from the repository root: python -m scripts.ollama_probe [--url URL]."""
import argparse
import json
from diagnostics import ollama_models


def main():
    parser = argparse.ArgumentParser(description="Read-only Ollama model discovery")
    parser.add_argument("--url", default="http://localhost:11434")
    args = parser.parse_args()
    try:
        models = ollama_models(args.url)
    except Exception:
        print(json.dumps({"reachable": False, "error": "Model discovery failed; check URL and service."}))
        return 1
    print(json.dumps({"reachable": True, "models": models}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
