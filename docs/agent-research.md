# Agent setup research — 2026-11-16

## Findings and choices

Orion had no skill discovery, activation, tests, or project agent instructions. Its response methods accepted history but did not pass it to the model. Its requirements allowed current Pydantic AI while its code used older APIs.

The Agent Skills specification defines a portable SKILL.md with YAML name and description. Its integration guide recommends a compact catalog and on-demand activation. Orion will adopt this format, use a dedicated read-only activation tool, and keep scripts outside automatic execution.

Sources reviewed:

- https://agentskills.io/specification — metadata, names, and directory format.
- https://agentskills.io/integrate-skills — catalog, activation, trust, and progressive disclosure.
- https://skills.sh/ — discovery only; popularity is not a correctness check.
- https://github.com/anthropics/skills — skill packaging examples. Inspected revision: 1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064.
- https://ai.pydantic.dev/agents/ — current agent lifecycle and tools.
- https://github.com/pydantic/pydantic-ai/tree/main/.agents/skills — contributor workflows. Inspected revision: c7586d79b64706f4605f15a29534118813df12a4.

The upstream packs contain broad design, document, and contributor workflows. Those do not fit Orion's small Python/Ollama client as a bulk install. Use original, short Orion skills based on the documented patterns instead. No upstream skill text or code is copied, so no third-party license material is vendored.

## Ten improvements

1. Project context and agent guidance.
2. A bounded, validated local skill registry.
3. Current Pydantic AI lifecycle and reproducible dependencies.
4. Runtime skill catalog and activation.
5. A source-based research skill.
6. An Ollama diagnostic skill and read-only probe.
7. An MCP setup skill and configuration checks.
8. Conversation history passed to the model.
9. Atomic, private local settings storage.
10. A release evaluation skill and offline CI checks.

Validation uses offline behavior tests. Live Ollama/MCP access and manual rendered UI checks remain separate evidence. No claim of improved answer quality or latency is made without a matched live evaluation.
