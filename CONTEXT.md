# Orion context

Orion is a Streamlit chat client. `app.py` owns the UI and Pydantic AI agent. Ollama serves the model through its OpenAI-compatible endpoint. An optional MCP server supplies external tools.

A **skill** is task guidance stored as `.agents/skills/<name>/SKILL.md`. A **tool** is an executable capability registered with the agent. Loading a skill must not execute its scripts or create new permissions.

`orion_settings.json` is local personal configuration and is ignored by Git. Environment variables supply optional MCP defaults. User input must remain separate from system instructions.

Keep startup and automated tests usable without live services. Verify a real service before claiming it is connected.
