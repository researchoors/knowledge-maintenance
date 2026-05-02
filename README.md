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

### DarkBloom Spec Pipeline

The generated spec lives under [`spec/`](spec/) as an mdBook scaffold. It is derived from the committed flashlight artifacts under [`artifacts/d-inference`](artifacts/d-inference), not from hand-written claims.

Local regeneration:

```bash
python scripts/extract_facts.py
python scripts/render_spec.py
python scripts/verify_spec.py
cargo install mdbook mdbook-mermaid --locked  # first run only
mdbook build spec
```

CI uploads the built mdBook (`spec/book`) as the `darkbloom-spec-mdbook` workflow artifact on every run. The book uses `mdbook-mermaid` so architecture, lifecycle, and sequence diagrams render as diagrams rather than fenced code blocks. After changes are merged to `main`, the same workflow deploys the built book to GitHub Pages.

Pipeline contract:

1. **Evidence is autonomous**: `.github/workflows/darkbloom-spec.yml` can run `github-flashlight` and open/update an artifact-only PR (`automation/darkbloom-artifacts`).
2. **Facts/spec are autonomous derived commits**: the workflow extracts `facts/darkbloom.facts.json`, renders `spec/src/*.md`, verifies source comments and mdBook summary links, runs tests, and opens/updates a separate derived PR (`automation/darkbloom-derived-spec`).
3. **Runner egress is controlled**: autonomous jobs install [`ironsh/iron-proxy-action`](https://github.com/ironsh/iron-proxy-action), enforce default-deny outbound HTTP(S), and use [`egress-rules.yaml`](egress-rules.yaml) as the explicit allowlist. The action summary is uploaded on every run for auditability.
4. **Canonical merge is human-gated**: automation opens PRs only. It does not auto-merge. Reviewers decide when artifact truth and derived spec updates become canonical.

Every generated normative bullet includes a source comment like `<!-- source: artifacts/...#L1-L2 fact: abc123 -->` so reviewers can trace spec text back to flashlight evidence.

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
