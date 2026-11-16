---
name: ollama-diagnostics
description: Diagnose Orion model discovery, Ollama connection failures, or missing models without changing the service.
license: MIT
---

Check the configured URL and exact model name first. Orion uses `/api/tags` for discovery and `/v1` for OpenAI-compatible model requests. A listed model does not prove generation or tool calling works.

If a shell is available and the task authorizes a connection check, run `.venv/bin/python -m scripts.ollama_probe --url <configured-url>` from the Orion root. This sends only a model-list GET, with a five-second timeout. If no shell is available, ask the user to run it and share its JSON output. Do not claim the script ran without a tool result.

Interpret reachable=false as discovery failure, not proof the model is absent. For an empty list, explain that the server responded but returned no named models. Match exact tags before suggesting a model switch. Do not pull models, restart services, or change hosts unless requested.

After discovery, test a short generation only when needed and authorized. For skill failures, separately check that the selected model supports tool calls. Report discovery, generation, and tool activation as separate results.
