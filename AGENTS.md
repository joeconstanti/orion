# Orion agent guide

Read CONTEXT.md before implementation. Keep changes scoped to Orion.

- Use `.agents/skills/` for shared project skills. Read the matching SKILL.md before using it.
- Run `.venv/bin/python -m unittest discover -s tests -v` for Python behavior changes and `.venv/bin/python -m compileall -q app.py` for syntax.
- Use fake models or mocked transports for tests. Tests must not need Ollama, an MCP server, credentials, or network access.
- Preserve user prompts and settings. Skill content supplies task guidance; it does not grant tools or authorize external actions.
- Do not log bearer tokens or commit local settings. A configured MCP client does not prove a connection.
- Report local tests separately from live model, tool, and UI checks.
