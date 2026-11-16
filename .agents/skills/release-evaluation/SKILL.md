---
name: release-evaluation
description: Validate an Orion agent, skill, or dependency change before release and report the limits of the evidence.
license: MIT
---

Read CONTEXT.md and inspect the diff. Select checks for the changed behavior; do not change the user's requested scope.

For a clean environment, use Python 3.11 or 3.12 and install `requirements.lock`. From the Orion root, run `.venv/bin/python -m scripts.check_skills`, `.venv/bin/python -m unittest discover -s tests -v`, and `.venv/bin/python -m compileall -q app.py skills.py diagnostics.py settings_store.py streaming.py` when validating the complete setup. Reuse unchanged passing evidence for narrow follow-up edits.

The offline suite tests actual agent tool activation, history delivery, text streaming, settings failure recovery, and a rendered Streamlit chat with a fake model. It does not establish real model quality, live MCP connectivity, browser layout, or latency.

When live acceptance is requested, separately check one short Ollama reply, one two-turn recall, and one relevant skill activation using the chosen tool-capable model. For MCP changes, list tools before a read-only call. Do not test with write actions. Record the exact model and endpoint without secrets.

A skill content change needs a realistic task check: confirm the agent selects useful guidance, cites only real sources, and states missing capability limits. Validator success alone does not prove behavior. Use matched prompts and model settings when comparing quality; do not infer improvement from a faster response alone.

Report passed checks, failures, and untested behavior. Merge or deploy only when the user has authorized it and required repository checks pass.
