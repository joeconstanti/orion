# Orion

<div align="center">

![Made by Joe](https://img.shields.io/badge/Made%20by-Joe-red?style=for-the-badge)
![Local AI](https://img.shields.io/badge/AI-Ollama-orange?style=for-the-badge)
![Agent Skills](https://img.shields.io/badge/Agent-Skills-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)

[![Agent Checks](https://github.com/joeconstanti/orion/actions/workflows/agent-checks.yml/badge.svg)](https://github.com/joeconstanti/orion/actions/workflows/agent-checks.yml)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

**Chat with Ollama models through a Streamlit interface. Add task guidance with local skills and connect external tools through MCP.**

[Features](#features) • [Quick Start](#quick-start) • [Project Skills](#project-skills) • [Report Bug](https://github.com/joeconstanti/orion/issues)

</div>

## Features

<div align="center">

| Feature | What it does |
|---------|--------------|
| **Ollama models** | Discovers models from your configured server and uses its OpenAI-compatible endpoint |
| **Streaming chat** | Displays replies as they arrive and passes prior chat turns to the model |
| **Explicit thinking tags** | Separates a leading `<think>...</think>` block from the answer when the model emits one |
| **Project skills** | Loads a compact catalog and supplies full instructions through the read-only `activate_skill` tool |
| **Optional MCP tools** | Connects to a configured MCP server, with optional bearer authentication |
| **Custom instructions** | Lets you edit the system prompt and change model and server settings |
| **Local settings** | Saves configuration with atomic replacement and private file permissions on POSIX |
| **Offline validation** | Tests agent behavior and a rendered Streamlit chat using fake models and transports |

</div>

Chat history is held in the Streamlit session. Settings are saved locally; chat
history is not stored in a persistent conversation database. Ollama can run on
this machine or another host. Connected MCP tools may use external services.

## Project Skills

| Skill | Outcome | Requirements |
|-------|---------|--------------|
| **[source-research](.agents/skills/source-research/SKILL.md)** | Source-based research with dates, direct links and stated uncertainty | Supplied sources or an available research tool |
| **[ollama-diagnostics](.agents/skills/ollama-diagnostics/SKILL.md)** | Separates model discovery, generation and tool-support checks | Access to the configured Ollama server; optional shell probe |
| **[mcp-setup](.agents/skills/mcp-setup/SKILL.md)** | Guides endpoint, authentication and tool-availability diagnosis | Server documentation and an available MCP client for live checks |
| **[release-evaluation](.agents/skills/release-evaluation/SKILL.md)** | Selects relevant checks and reports their evidence limits | Repository access and Python for local validation |

Ask in chat, for example: “Use source-research to compare these agent tools.”
Orion gives the model a catalog of skill names and descriptions. A model that
supports tool calls can request the full instructions with `activate_skill`.
These are task instructions, not built-in slash commands.

Skills do not add executable capabilities. Loading one does not run its scripts,
install dependencies or grant access to external services. Tools come from the
connected MCP server; Orion does not bundle the server-specific research, email,
calendar or media tools.

See the [agent research record](docs/agent-research.md) for sources and adoption
decisions.

## Technologies Used

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Markdown](https://img.shields.io/badge/Markdown-000000?style=flat-square&logo=markdown&logoColor=white)

</div>

| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Application and validation scripts; CI covers Python 3.11 and 3.12 |
| **Streamlit** | Chat interface, sidebar settings and session state |
| **Pydantic AI** | Agent runs, model messages, skill activation and MCP toolsets |
| **Ollama** | Model serving through an OpenAI-compatible API |
| **MCP** | Optional connection to external tools |
| **PyYAML + SKILL.md** | Validated metadata and portable task guidance |
| **HTTPX** | Timed, read-only Ollama model discovery |

## Project Structure

```text
orion/
├── app.py                       # Streamlit UI and Pydantic AI agent
├── skills.py                    # Local skill registry and activation
├── streaming.py                 # Explicit thinking-tag and answer separation
├── diagnostics.py               # Service URL validation and model discovery
├── settings_store.py            # Validated, atomic local settings storage
├── .agents/skills/              # Four bundled SKILL.md workflows
├── scripts/
│   ├── check_skills.py          # Complete bundled catalog validation
│   └── ollama_probe.py          # Read-only model discovery CLI
├── tests/                       # Offline agent, storage and Streamlit tests
├── docs/agent-research.md        # Research sources and integration decisions
├── .github/workflows/           # Python test matrix
├── AGENTS.md                    # Coding-agent guidance
├── CONTEXT.md                   # Project terms and boundaries
├── requirements.txt             # Direct application dependencies
├── requirements.lock            # Tested dependency snapshot
└── LICENSE
```

## Local Development

### Quick Start

Install [Ollama](https://ollama.com) and Python 3.11 or 3.12, then set up Orion:

```sh
git clone https://github.com/joeconstanti/orion.git
cd orion
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Start Ollama if it is not already running:

```sh
ollama serve
```

In another terminal, pull the default model:

```sh
ollama pull qwen3:14b
```

From the activated Orion environment, start the app:

```sh
streamlit run app.py
```

Open `http://localhost:8501`. Use the sidebar to select a model or change the
Ollama server URL. The default server is `http://localhost:11434`.

### Agent Support

Orion discovers `.agents/skills/<name>/SKILL.md` relative to the application at
startup. Each file needs YAML `name` and `description` fields followed by Markdown
instructions. The name must match its directory. Restart Orion after a skill edit.

Keep this directory limited to reviewed skills. The registry skips symlinked,
invalid and oversized skill files, and limits the loaded catalog to 50 skills.
Diagnostics are available through the application's `skills.diagnostics` attribute
and the bundled catalog check below.

Coding agents that support `.agents/skills/` can also discover these files.
Other clients can read the canonical SKILL.md directly. This repository does not
install provider-specific command adapters or global skills.

### Validation

Run from the activated environment:

```sh
python -m pip check
python -m scripts.check_skills
python -m unittest discover -s tests -v
python -m compileall -q app.py skills.py diagnostics.py settings_store.py streaming.py
```

The offline suite checks actual agent tool activation, history delivery,
streaming, settings recovery and a rendered Streamlit chat with a fake model.
CI runs the checks on Python 3.11 and 3.12. These checks do not establish live
Ollama quality, MCP connectivity or browser layout.

For model discovery alone:

```sh
python -m scripts.ollama_probe --url http://localhost:11434
```

This sends a model-list GET with a five-second timeout and returns JSON. A listed
model does not prove generation or tool calling works.

## Customization

Change the Ollama model, server URL, MCP settings and system prompt in the sidebar.
Apply settings to save them to the ignored `orion_settings.json` file.

Optional MCP defaults can be supplied in an ignored `.env` file:

```env
MCP_SERVER_URL=https://your-mcp-server.example/mcp
MCP_BEARER_TOKEN=your_bearer_token
```

Use the endpoint documented by your server. Authentication is optional when the
server allows it. Saved values override environment defaults, including an empty
MCP URL, which disables MCP. “Configured” means the client is set up; it does not
mean a connection has been tested.

Settings remain local plaintext. Writes use atomic replacement and owner-only
permissions on POSIX. Keep tokens out of commits and shared logs.

### Troubleshooting

| Symptom | Next check |
|---------|------------|
| **Model discovery fails** | Check the configured URL and Ollama service, then run the probe |
| **Selected model is absent** | Compare its exact tag with `ollama list` on the server |
| **Skill does not activate** | Check the catalog and confirm that the selected model supports tool calls |
| **MCP tools are unavailable** | Confirm the documented endpoint, authentication and a successful tool-list operation |
| **No thinking block appears** | The model may return a direct answer; only explicit leading thinking tags are separated |
| **Settings cannot be saved** | Check local file access and available disk space |

## Contributing

<div align="center">

![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen?style=for-the-badge)
[![Issues](https://img.shields.io/badge/Issues-Welcome-red?style=for-the-badge)](https://github.com/joeconstanti/orion/issues)

</div>

| Step | Action |
|------|--------|
| **Context** | Read `AGENTS.md` and `CONTEXT.md` before changing the app |
| **Branch** | Use a descriptive branch such as `fix/model-discovery` |
| **Change** | Keep the change scoped and preserve user prompts and local settings |
| **Validate** | Run the checks relevant to the changed behavior; keep automated tests independent of live services |
| **PR** | Explain the behavior change, actual validation and any untested live behavior |

Use `requirements.txt` for direct dependencies. Update and validate
`requirements.lock` when dependencies change. Keep skills short and distinguish
task guidance from executable tools.

## Acknowledgments

- [Pydantic AI](https://ai.pydantic.dev): agent framework and model integration.
- [Ollama](https://ollama.com): model serving.
- [Streamlit](https://streamlit.io): Python chat interface.
- [Model Context Protocol](https://modelcontextprotocol.io): external tool integration.
- [Agent Skills](https://agentskills.io): portable skill format and loading guidance.
- [jstack](https://github.com/joeconstanti/jstack): README structure and presentation reference.

The bundled skills are original Orion content. No upstream skill pack is vendored.

## License

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-green?style=for-the-badge)](https://github.com/joeconstanti/orion)

</div>

Orion is available under the [MIT License](LICENSE).

---

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/joeconstanti/orion?style=social)](https://github.com/joeconstanti/orion/stargazers)

**Made by [Joe](https://madebyjoe.co)**

[GitHub](https://github.com/joeconstanti/orion) • [Report Bug](https://github.com/joeconstanti/orion/issues)

</div>
