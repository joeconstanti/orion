# CI and offline validation

`Agent checks` runs the same offline checks on Python 3.11 and 3.12.
Use Python 3.11 or 3.12 and the pinned `requirements.lock` in a local `.venv`.

```sh
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip check
.venv/bin/python -m scripts.check_skills
(
  repo=$PWD
  test_dir=$(mktemp -d) || exit 1
  trap 'rm -rf -- "$test_dir"' EXIT
  cd "$test_dir" || exit 1
  PYTHON_DOTENV_DISABLED=1 MCP_SERVER_URL= MCP_BEARER_TOKEN= \
    PYTHONPATH="$repo" "$repo/.venv/bin/python" -m unittest discover -s "$repo/tests" -v
)
.venv/bin/python -m compileall -q app.py skills.py diagnostics.py settings_store.py streaming.py
```

These checks cover fake-model agent runs, skill loading, settings storage and
Streamlit AppTest behavior. They do not establish live Ollama generation, MCP
connectivity, browser layout, installed-app behavior or deployment health.
Never substitute a green build for acceptance evidence that requires a real service.

## Triggers and superseded runs

The workflow runs on pull requests and pushes to `main`. Feature-branch pushes
are not separately enabled: a PR update gets one workflow, with two Python jobs.
The `main` push after merging is an intentional integration check of the merged
commit, not a duplicate feature-branch check.

Concurrency is grouped by Git ref and cancels an older in-progress workflow for
the same PR or branch. Different PRs keep their independent results. Matrix
fail-fast may cancel the other Python job after one job fails; that cancellation
does not establish a second failure or a pass. Inspect the first failing job.

Keep code, tests, skills, dependency and workflow changes covered. No path filters
are applied, so a documentation PR still verifies that its stated setup works.
Do not disable the workflow, skip failing checks, or change notification settings
to conceal a failure. Fix its cause and push a new commit; distinguish old-head
failures from results on the current head. An unchanged rerun is appropriate only
when there is evidence of a transient infrastructure failure.

## Deterministic Streamlit tests

- The workflow starts the entire suite from a fresh working directory and
  disables dotenv discovery. This keeps settings reads and writes away from
  the checkout and prevents dotenv from finding a file beside `app.py`, even
  when the working directory has already changed.
- Use fake models and mocked discovery/transports. Tests must not need an Ollama
  service, MCP server, network access, credentials or personal settings.
- Put settings in a temporary working directory, restore the original directory
  in `finally`, and set explicit empty MCP environment defaults. Do not run these
  tests concurrently inside one Python process: working-directory changes and
  environment patches are process-wide.
- AppTest executes `app.py` as its own script module. Patching an imported
  `app.PydanticAIWebApp` does not replace that script's class. Inject response
  methods on the actual `session_state['app']` instance, or mock the dependency
  the script imports.
- Follow real widget interactions: after editing a value that enables a button,
  call `.run(timeout=20)` and reacquire the button before clicking it. AppTest
  correctly rejects clicking a disabled widget. A missing rerender caused a
  settings regression test to fail; the correction keeps its failure/retry
  assertions intact.
- Keep explicit test timeouts and behavior assertions. When a shared machine is
  overloaded, defer full local suites/AppTest runs until capacity is available;
  continue source review and hosted CI instead of increasing timeouts or
  repeatedly rerunning unchanged failures. Hosted evidence and local evidence
  must be reported separately.
