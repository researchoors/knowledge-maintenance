#!/usr/bin/env python3
"""Render a legible mdBook formal specification from DarkBloom artifacts.

The renderer is intentionally template-driven. Flashlight output is used as
source evidence, but artifact headings are not rendered as specification prose.
"""

# ruff: noqa: E501,I001

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from html import escape
from pathlib import Path
from typing import Any


REQ_SOURCES = {
    "system.role.coordinator": ("artifacts/d-inference/service_discovery/components.json", "L30-L87"),
    "system.role.provider": ("artifacts/d-inference/service_discovery/components.json", "L193-L315"),
    "system.role.web": ("artifacts/d-inference/service_discovery/components.json", "L103-L169"),
    "system.role.enclave": ("artifacts/d-inference/service_discovery/components.json", "L330-L339"),
    "system.role.analytics": ("artifacts/d-inference/service_discovery/components.json", "L4-L27"),
    "protocol.consumer-flow": ("artifacts/d-inference/architecture_docs/architecture.md", "L251-L276"),
    "protocol.provider-registration": ("artifacts/d-inference/architecture_docs/architecture.md", "L278-L312"),
    "protocol.payment-settlement": ("artifacts/d-inference/architecture_docs/architecture.md", "L314-L338"),
    "security.trust-model": ("artifacts/d-inference/architecture_docs/architecture.md", "L340-L376"),
    "security.crypto": ("artifacts/d-inference/service_analyses/darkbloom.md", "L48-L52"),
    "runtime.provider": ("artifacts/d-inference/service_analyses/darkbloom.md", "L210-L274"),
}


def req_comment(req_id: str) -> str:
    source_file, source_lines = REQ_SOURCES[req_id]
    return f"<!-- req: {req_id}; source: {source_file}#{source_lines} -->"


def bullet(req_id: str, text: str) -> str:
    return f"- {req_comment(req_id)} {text}"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_payload(path: Path) -> dict[str, Any]:
    return load_json(path)


def component_rows(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / "artifacts/d-inference/service_discovery/components.json"
    data = load_json(path)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for component in data.get("components", []):
        key = (component.get("name", ""), component.get("kind", ""), component.get("root_path", ""))
        if key in seen:
            continue
        seen.add(key)
        rows.append(component)
    return rows


def write_book_toml(book_dir: Path) -> None:
    (book_dir / "book.toml").write_text(
        """[book]
title = "DarkBloom Spec"
authors = ["DarkBloom Spec Pipeline"]
language = "en"
src = "src"

[output.html]
git-repository-url = "https://github.com/researchoors/darkbloom-spec"
""",
        encoding="utf-8",
    )


def write_summary(src: Path) -> None:
    lines = [
        "# Summary",
        "",
        "[Introduction](introduction.md)",
        "- [System Overview](overview.md)",
        "- [Architecture](architecture.md)",
        "- [Participants and Components](components.md)",
        "- [Protocol](protocol.md)",
        "  - [Provider Lifecycle](provider-lifecycle.md)",
        "  - [Inference Lifecycle](inference-lifecycle.md)",
        "- [Security and Trust](security.md)",
        "- [Operations](operations.md)",
        "- [Open Questions](open-questions.md)",
        "- [Evidence Index](evidence.md)",
        "",
    ]
    (src / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def write_intro(src: Path, payload: dict[str, Any]) -> None:
    source = payload.get("source", {})
    content = f"""# DarkBloom Specification

This book is a formal specification candidate for DarkBloom / d-inference. It is generated from committed
`github-flashlight` artifacts and is intended to be reviewed before becoming canonical project truth.

The generated prose is not a direct dump of flashlight output. The renderer projects evidence into a stable protocol
shape: actors, trust boundaries, message flows, runtime requirements, and open questions. Each normative requirement
carries a `req` comment that points back to the artifact span used as evidence.

## Source snapshot

- Source repository: `{source.get("source_repo")}`
- Source commit: `{source.get("source_commit")}`
- Flashlight analysis timestamp: `{source.get("analysis_timestamp")}`
- Artifact path: `{source.get("artifacts_path")}`

## Review model

Automation may refresh evidence and render this book, but canonical changes are merged only after human review.
Reviewers should treat `artifacts/d-inference/**` and `facts/darkbloom.facts.json` as provenance for the formal spec.
"""
    (src / "introduction.md").write_text(content, encoding="utf-8")


def write_overview(src: Path) -> None:
    content = f"""# System Overview

DarkBloom is a distributed inference system that routes AI inference work from consumers to Apple Silicon provider
machines. The system combines a coordinator control plane, provider runtimes, a web console, and Secure Enclave based
attestation components. Its central design objective is to let consumers use remote provider capacity while preserving
privacy and making provider trust auditable.

## Goals

{bullet("system.role.coordinator", "The coordinator is the control-plane service responsible for provider registry, request routing, attestation integration, and payment/accounting coordination.")}
{bullet("system.role.provider", "The DarkBloom provider runtime runs on Apple Silicon Macs and exposes local model capacity to the coordinator.")}
{bullet("system.role.web", "The web console provides consumer chat and provider dashboard surfaces and participates in end-to-end encryption and trust display.")}
{bullet("system.role.enclave", "Secure Enclave components provide hardware-backed signing and attestation support for provider identity and trust decisions.")}

## High-level architecture

```mermaid
flowchart LR
    Consumer[Consumer / API client]
    Web[Web console]
    Coord[Coordinator]
    Analytics[Analytics service]
    DB[(PostgreSQL)]
    Stripe[Stripe]
    Provider[DarkBloom provider]
    Backend[Local MLX backend]
    Enclave[Secure Enclave]
    R2[Cloudflare R2]

    Consumer --> Web
    Consumer --> Coord
    Web --> Coord
    Coord --> DB
    Analytics --> DB
    Coord --> Stripe
    Coord <--> Provider
    Provider --> Backend
    Provider --> Enclave
    Provider --> R2
```

## Trust boundaries

- Consumer-facing clients interact with the coordinator and web console over network APIs.
- Provider nodes are independently operated Apple Silicon machines and are treated as untrusted until registered and attested.
- The coordinator routes and accounts for work but the architecture is designed around encrypted inference payloads.
- Secure Enclave keys and attestation material are part of the provider trust boundary, not a general-purpose application secret store.

## Specification status

This book currently specifies the implementation-derived protocol at the level supported by available flashlight evidence.
Open questions are called out explicitly where artifacts do not contain enough detail to make a normative statement.
"""
    (src / "overview.md").write_text(content, encoding="utf-8")


def write_architecture(src: Path) -> None:
    content = f"""# Architecture

This section specifies the major runtime domains and the way work moves through them.

## Runtime domains

```mermaid
flowchart TB
    subgraph Client[Consumer domain]
      API[OpenAI-compatible API clients]
      Browser[Web console]
    end

    subgraph Control[Control plane]
      Coordinator[Coordinator service]
      Ledger[Payment ledger]
      Registry[Provider registry]
      Attestation[Attestation verifier]
    end

    subgraph ProviderDomain[Provider domain]
      App[EigenInference app]
      Agent[DarkBloom provider agent]
      Engine[Inference backend]
      SE[Secure Enclave]
    end

    subgraph External[External services]
      Postgres[(PostgreSQL)]
      Stripe[Stripe]
      Datadog[Datadog]
      R2[Cloudflare R2]
      Apple[Apple services]
    end

    API --> Coordinator
    Browser --> Coordinator
    Coordinator --> Registry
    Coordinator --> Ledger
    Coordinator --> Attestation
    Coordinator --> Postgres
    Coordinator --> Stripe
    Coordinator --> Datadog
    App --> Agent
    Agent <--> Coordinator
    Agent --> Engine
    Agent --> SE
    Agent --> R2
    SE --> Apple
```

## Architectural requirements

{bullet("system.role.coordinator", "The coordinator MUST maintain enough provider state to route inference requests to eligible providers.")}
{bullet("system.role.provider", "The provider runtime MUST manage local model/backend lifecycle before it can service assigned inference work.")}
{bullet("system.role.analytics", "Analytics components SHOULD consume read-only or derived operational state rather than acting as request-routing authorities.")}
{bullet("system.role.web", "The web console MAY expose both consumer and provider-facing views, but it is not the provider runtime.")}

## Separation of concerns

- The coordinator owns global routing, provider registry, payment/accounting, and policy checks.
- Providers own local hardware detection, model discovery, inference backend lifecycle, and response streaming.
- Secure Enclave components own hardware-backed key and attestation operations.
- Analytics is observational and should not be on the critical inference routing path.
"""
    (src / "architecture.md").write_text(content, encoding="utf-8")


def write_components(src: Path, repo_root: Path) -> None:
    rows = component_rows(repo_root)
    lines = [
        "# Participants and Components",
        "",
        "This section lists implementation components discovered from the flashlight service-discovery artifact.",
        "",
        "| Component | Kind | Type | Root | Role |",
        "|---|---:|---:|---|---|",
    ]
    for component in rows:
        name = escape(str(component.get("name", "")), quote=False)
        kind = escape(str(component.get("kind", "")), quote=False)
        typ = escape(str(component.get("type", "")), quote=False)
        root = escape(str(component.get("root_path", "")), quote=False)
        desc = escape(str(component.get("description", "")), quote=False)
        lines.append(f"| `{name}` | {kind} | {typ} | `{root}` | {desc} |")

    lines.extend(
        [
            "",
            "## Component requirements",
            "",
            bullet(
                "system.role.coordinator",
                "Coordinator components MUST be treated as control-plane components for routing, attestation integration, and accounting.",
            ),
            bullet(
                "system.role.provider",
                "The `darkbloom` provider component MUST be treated as the provider-side runtime for Apple Silicon inference capacity.",
            ),
            bullet(
                "system.role.enclave",
                "The `EigenInferenceEnclave` components MUST be treated as the provider-side hardware-attestation and signing boundary.",
            ),
            bullet(
                "system.role.web",
                "The `web` component SHOULD be treated as the user-facing interface, not as a source of provider attestation truth.",
            ),
            "",
        ]
    )
    (src / "components.md").write_text("\n".join(lines), encoding="utf-8")


def write_protocol(src: Path) -> None:
    content = f"""# Protocol

The DarkBloom protocol coordinates consumers, a central coordinator, and provider runtimes. This section defines the
observable protocol surfaces that are supported by current flashlight evidence.

## Protocol surfaces

| Surface | Participants | Purpose |
|---|---|---|
| Consumer API | Consumer/Web ↔ Coordinator | Submit inference work and receive streamed output. |
| Provider WebSocket | Provider ↔ Coordinator | Register capacity, receive assigned work, stream lifecycle events, and answer attestation challenges. |
| Attestation exchange | Coordinator ↔ Provider/Secure Enclave | Establish and refresh provider trust state. |
| Settlement flow | Consumer/Stripe/Coordinator/Provider | Reserve balance, record usage, credit providers, and process withdrawals. |

## Provider-to-coordinator messages

{bullet("runtime.provider", "Provider runtimes expose registration, heartbeat, inference lifecycle, error, cancellation, and attestation-response behavior over their coordinator protocol surface.")}
{bullet("protocol.provider-registration", "A provider MUST complete registration and trust establishment before it is eligible for routed inference work.")}

## Consumer inference flow

{bullet("protocol.consumer-flow", "A consumer inference request flows through the web/API surface to the coordinator, from the coordinator to an assigned provider, and back as streamed response chunks.")}
{bullet("security.crypto", "Inference payload handling MUST preserve the cryptographic boundary described by the provider cryptography layer when encrypted request mode is used.")}

## Settlement flow

{bullet("protocol.payment-settlement", "The coordinator records payment settlement state after inference completion and provider withdrawal events.")}

## Open schema gaps

The artifacts identify message names and flows, but they do not yet provide complete wire schemas for all provider
messages. Those schemas should be added as explicit protocol tables once source artifacts contain enough detail.
"""
    (src / "protocol.md").write_text(content, encoding="utf-8")


def write_provider_lifecycle(src: Path) -> None:
    content = f"""# Provider Lifecycle

Provider lifecycle covers the path from local runtime startup to eligibility for inference assignment.

## Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Installed
    Installed --> Configured: provider config exists
    Configured --> Connected: WebSocket connection established
    Connected --> Registered: registration accepted
    Registered --> Attested: trust material verified
    Attested --> Available: capacity advertised
    Available --> Assigned: coordinator sends inference work
    Assigned --> Available: completion/error reported
    Available --> Disconnected: connection lost
    Disconnected --> Connected: reconnect
```

## Requirements

{bullet("runtime.provider", "A provider runtime MUST initialize local hardware, security, model, and backend state before advertising useful capacity.")}
{bullet("protocol.provider-registration", "A provider MUST register with the coordinator before it can be considered available for inference assignment.")}
{bullet("security.trust-model", "The coordinator SHOULD use attestation and security posture to determine provider trust level before routing sensitive work.")}
{bullet("system.role.enclave", "Secure Enclave signing material SHOULD be used for provider identity and attestation operations where available.")}

## Failure handling

- A disconnected provider is not eligible for new work until it reconnects and restores required state.
- A provider that fails attestation should remain in a lower trust state or be excluded from sensitive workloads.
- Runtime failures during assigned work should be reported through the provider lifecycle error path.
"""
    (src / "provider-lifecycle.md").write_text(content, encoding="utf-8")


def write_inference_lifecycle(src: Path) -> None:
    content = f"""# Inference Lifecycle

The inference lifecycle specifies the route from consumer request to provider execution and streamed completion.

## Flow

```mermaid
sequenceDiagram
    participant Consumer
    participant Web as Web/API Client
    participant Coordinator
    participant Provider
    participant Backend as Local Backend

    Consumer->>Web: Submit inference request
    Web->>Coordinator: Send request envelope
    Coordinator->>Coordinator: Authenticate, rate-limit, and select provider
    Coordinator->>Provider: Assign inference request
    Provider->>Backend: Forward/decrypt request for local execution
    Backend-->>Provider: Stream model output
    Provider-->>Coordinator: ResponseChunk events
    Coordinator-->>Web: Stream response
    Web-->>Consumer: Render output
    Provider->>Coordinator: Complete or Error
```

## Requirements

{bullet("protocol.consumer-flow", "The coordinator MUST select an eligible provider before forwarding an inference request to provider runtime execution.")}
{bullet("runtime.provider", "The provider runtime MUST bridge assigned inference work to a local inference backend and stream lifecycle results back to the coordinator.")}
{bullet("security.crypto", "Encrypted inference requests MUST be decrypted only within the provider-side cryptographic/runtime boundary described by the provider artifacts.")}
{bullet("protocol.payment-settlement", "Usage accounting SHOULD occur after completion/error reporting so settlement reflects executed work.")}

## Completion states

An assigned inference request should terminate in exactly one externally visible terminal state:

- `Complete`: the provider finished streaming output.
- `Error`: the provider failed the request.
- `Cancel`: the request was canceled before normal completion.

The artifacts do not yet define a complete state machine for retries or reassignment after provider failure.
"""
    (src / "inference-lifecycle.md").write_text(content, encoding="utf-8")


def write_security(src: Path) -> None:
    content = f"""# Security and Trust

DarkBloom's security model combines transport security, encrypted inference payloads, provider runtime hardening, and
Apple Secure Enclave based attestation.

## Trust model

{bullet("security.trust-model", "Provider trust MUST be evaluated as a graduated state rather than a binary property when attestation and software security posture are available.")}
{bullet("system.role.enclave", "Secure Enclave components MUST protect provider signing keys used for hardware-backed attestation and identity operations.")}
{bullet("security.crypto", "The provider cryptographic layer MUST protect inference request/response payloads when encrypted operation is used.")}
{bullet("runtime.provider", "Provider runtimes SHOULD apply local hardening controls before serving assigned inference work.")}

## Attestation flow

```mermaid
sequenceDiagram
    participant Coordinator
    participant Provider
    participant Enclave as Secure Enclave

    Provider->>Enclave: Create or load attestation key
    Provider->>Coordinator: Register with attestation material
    Coordinator->>Coordinator: Validate provider record and trust state
    Coordinator->>Provider: AttestationChallenge
    Provider->>Enclave: Sign challenge material
    Enclave-->>Provider: Signature
    Provider-->>Coordinator: AttestationResponse
    Coordinator->>Coordinator: Verify freshness and update trust level
```

## Threat boundaries

- The coordinator is trusted for routing and accounting, but encrypted inference mode limits plaintext exposure.
- Providers are independently operated and must be attested/hardened before receiving sensitive work.
- Web clients must not be treated as hardware-attestation authorities.
- Analytics consumers should not receive secrets or plaintext inference payloads.

## Open security questions

- What exact fields are signed in provider attestation blobs?
- What freshness window is required for challenge-response validation?
- Which trust levels are eligible for which classes of inference workload?
"""
    (src / "security.md").write_text(content, encoding="utf-8")


def write_operations(src: Path) -> None:
    content = f"""# Operations

Operational behavior covers provider installation, model/backend management, telemetry, accounting, and service health.

## Provider operations

{bullet("runtime.provider", "Provider operators SHOULD use the DarkBloom runtime to initialize hardware detection, configure model backends, manage lifecycle, inspect status, and report errors.")}
{bullet("system.role.provider", "Provider runtimes MAY integrate with macOS launchd, Cloudflare R2, Hugging Face model storage, and local MLX backends as operational dependencies.")}

## Coordinator operations

{bullet("system.role.coordinator", "Coordinator operators MUST maintain backing state for provider registry, attestation status, request routing, and payment/accounting records.")}
{bullet("protocol.payment-settlement", "Settlement operations SHOULD preserve a traceable relationship between consumer billing events, inference completion, provider credit, and withdrawal state.")}

## Observability

{bullet("system.role.analytics", "Analytics services SHOULD use read-only or pseudonymized data paths for network statistics and leaderboards.")}

## Operational diagram

```mermaid
flowchart LR
    Provider[Provider operator]
    Runtime[DarkBloom runtime]
    Model[Model cache/backend]
    Telemetry[Telemetry]
    Coordinator[Coordinator]
    Ledger[Ledger]
    Analytics[Analytics]

    Provider --> Runtime
    Runtime --> Model
    Runtime --> Telemetry
    Runtime <--> Coordinator
    Coordinator --> Ledger
    Coordinator --> Analytics
```
"""
    (src / "operations.md").write_text(content, encoding="utf-8")


def write_open_questions(src: Path) -> None:
    content = """# Open Questions

The current flashlight artifacts support a high-level implementation-derived specification, but several areas need
explicit source-backed schemas before they can become fully normative.

## Protocol schemas

- What is the canonical wire schema for provider `Register` messages?
- What fields are required in `Heartbeat`, `InferenceRequest`, `ResponseChunk`, `Complete`, `Error`, and `Cancel` messages?
- Are provider registration and reconnection idempotent?

## Trust and attestation

- What exact fields are bound into Secure Enclave signatures?
- What nonce freshness and replay-prevention rules are required?
- Which trust levels map to which routing decisions?

## Settlement

- What exact unit of usage is billed?
- What are the rounding and precision rules for provider credits?
- Which settlement events are terminal and which are retryable?

## Versioning

- How are protocol-breaking changes negotiated between coordinator and provider runtimes?
- What compatibility guarantees exist for older provider binaries?
"""
    (src / "open-questions.md").write_text(content, encoding="utf-8")


def render_statement(statement: str) -> str:
    return escape(statement.rstrip("."), quote=False) + "."


def source_comment(fact: dict[str, Any]) -> str:
    return f"<!-- source: {fact['source_file']}#{fact['source_lines']} fact: {fact['id']} -->"


def write_evidence(src: Path, payload: dict[str, Any]) -> None:
    facts = payload["facts"]
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        if fact.get("kind") == "section":
            continue
        by_file[fact["source_file"]].append(fact)

    lines = [
        "# Evidence Index",
        "",
        "This appendix indexes non-heading evidence extracted from flashlight artifacts. It is provenance, not the spec itself.",
        "",
    ]
    for source_file in sorted(by_file):
        lines.extend([f"## `{source_file}`", ""])
        for fact in by_file[source_file][:80]:
            title = escape(str(fact["title"]), quote=False)
            lines.append(f"- {source_comment(fact)} **{title}** — {render_statement(fact['statement'])}")
        if len(by_file[source_file]) > 80:
            lines.append(
                f"- ... {len(by_file[source_file]) - 80} additional facts omitted from this rendered appendix."
            )
        lines.append("")
    (src / "evidence.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, default=Path("facts/darkbloom.facts.json"))
    parser.add_argument("--book", type=Path, default=Path("spec"))
    args = parser.parse_args()

    repo_root = Path.cwd()
    payload = load_payload(args.facts)
    src = args.book / "src"
    src.mkdir(parents=True, exist_ok=True)

    write_book_toml(args.book)
    write_summary(src)
    write_intro(src, payload)
    write_overview(src)
    write_architecture(src)
    write_components(src, repo_root)
    write_protocol(src)
    write_provider_lifecycle(src)
    write_inference_lifecycle(src)
    write_security(src)
    write_operations(src)
    write_open_questions(src)
    write_evidence(src, payload)
    print(f"rendered formal DarkBloom specification into {args.book}")


if __name__ == "__main__":
    main()
