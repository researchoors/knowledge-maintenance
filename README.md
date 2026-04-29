# knowledge-maintenance

Knowledge graph maintenance for [d-inference (DarkBloom)](https://github.com/Layr-Labs/d-inference) — auto-generated architecture docs, temporal validation, and discrepancy tracking via [github-flashlight](https://github.com/Layr-Labs/github-flashlight).

## How it works

### Flashlight Sweep (`every 6h`)

1. Reads [`tracked-repos.yaml`](tracked-repos.yaml) for repos to monitor
2. Checks each repo's HEAD SHA against the last analyzed commit in `manifest.json`
3. If changed, runs `flashlight` against the repo
4. Commits updated artifacts to a branch and **opens a PR** for review

### Temporal Validation (`daily 08:00 UTC`)

1. Reads stored artifacts for each tracked repo
2. Clones the source repo at the analyzed commit
3. Runs deterministic checks: stale references, missing components, stale edges, kind mismatches
4. If discrepancies found, opens/updates a GitHub issue with the report

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

## Linting

```bash
ruff check .
ruff format --check .
```

## Configuration

Set in `.env` or environment variables (prefixed with `KM_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `KM_REPO_URL` | `https://github.com/Layr-Labs/d-inference` | Source repo to track |
| `KM_REPO_BRANCH` | `main` | Branch to track |
| `KM_LLM_BASE_URL` | `https://api.openai.com/v1` | LLM endpoint for stale_claim checks |
| `KM_LLM_MODEL` | `gpt-4o-mini` | LLM model |
| `KM_LLM_API_KEY` | _(empty = skip LLM checks)_ | LLM API key |

## Adding a new repo

Add an entry to `tracked-repos.yaml`:

```yaml
repos:
  - repo: Layr-Labs/d-inference
    artifacts_path: artifacts/d-inference
    public: true
```

For private repos, set `public: false` and add `FLASHLIGHT_REPO_TOKEN` as a repository secret.
