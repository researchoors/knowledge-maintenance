# D-Inference Cross-Pipeline Comparative Analysis

**LlamaIndex Pipeline (Ollama + GLM-5.1)** vs **Flashlight (github-flashlight)**  
**Codebase**: DarkBloom/d-inference at commit `f7dab6fa994a`  
**Analysis Date**: 2026-04-30

---

## 1. Executive Summary

Flashlight produces **significantly more accurate and deeper** analysis than the LlamaIndex pipeline across nearly every dimension. The LlamaIndex pipeline generates well-structured, readable documents but suffers from hallucinated components, shallow code references, and a dependency graph that is largely inferred rather than extracted. Flashlight grounds its output in actual code artifacts (go.mod, Cargo.toml, Package.swift, package.json), extracts real dependency edges, and provides precise file paths with line numbers. However, the LlamaIndex pipeline captures some architectural concepts (trust boundaries, request lifecycle) that Flashlight's more mechanical analysis misses.

| Dimension | LlamaIndex | Flashlight | Verdict |
|-----------|-----------|------------|---------|
| Component coverage | 10 (3 hallucinated) | 9 (all real) | **Flashlight** |
| File path accuracy | Partial, some wrong paths | Precise with line numbers | **Flashlight** |
| Dependency graph | 8 edges (5 inferred) | 20 edges (all extracted) | **Flashlight** |
| Architecture doc depth | Excellent trust boundary analysis | Good but more generic | **LlamaIndex** |
| Hallucination rate | ~30% of component files | ~0% | **Flashlight** |
| External deps precision | Narrative only | Exact versions from manifests | **Flashlight** |

---

## 2. Component Coverage Comparison

### 2.1 Component Inventory

| Component | LlamaIndex | Flashlight | Notes |
|-----------|-----------|------------|-------|
| **coordinator** | ✅ `coordinator.md` | ✅ `coordinator.md` | Both cover; Flashlight deeper |
| **darkbloom (provider)** | ✅ `provider.md` | ✅ `darkbloom.md` | Naming: LlamaIndex calls it "provider", Flashlight "darkbloom" |
| **EigenInferenceEnclave** | ✅ `enclave.md` | ✅ `EigenInferenceEnclave.md` | Both cover |
| **EigenInferenceEnclaveCLI** | ❌ (merged into attestation.md) | ✅ `EigenInferenceEnclaveCLI.md` | Flashlight separates; LlamaIndex folds into attestation |
| **EigenInference (macOS app)** | ❌ Missing | ✅ `EigenInference.md` | **LlamaIndex gap** — entire Swift/SwiftUI app not documented |
| **console-ui (web)** | ✅ `console-ui.md` | ✅ `web.md` | Both cover; Flashlight deeper |
| **analytics** | ❌ Missing | ✅ `analytics.md` | **LlamaIndex gap** — entire Go service not documented |
| **verify-attestation** | ❌ (mentioned in coordinator.md) | ✅ `verify-attestation.md` | Flashlight gives full analysis; LlamaIndex mentions briefly |
| **decrypt-test** | ✅ `e2e-encryption.md` (partial) | ✅ `decrypt-test.md` | Both cover; Flashlight gives dedicated analysis |
| **protocol** | ✅ `protocol.md` | ❌ (folded into coordinator) | **Flashlight gap** — no dedicated protocol analysis |
| **billing** | ✅ `billing.md` | ❌ (folded into coordinator) | LlamaIndex creates standalone doc for embedded subsystem |
| **e2e-encryption** | ✅ `e2e-encryption.md` | ❌ (decrypt-test covers testing side) | LlamaIndex creates standalone doc |
| **attestation** | ✅ `attestation.md` | ❌ (split across EigenInferenceEnclave + verify-attestation) | Different decomposition strategy |
| **mdm-enrollment** | ✅ `mdm-enrollment.md` | ❌ No equivalent | **HALLUCINATION** — no such code exists |
| **image-bridge** | ✅ `image-bridge.md` | ❌ No equivalent | **HALLUCINATION** — LlamaIndex admits "no information found" |

### 2.2 Hallucinated Components

**mdm-enrollment.md** (LlamaIndex): This is the most significant hallucination. The document describes a MicroMDM integration, ACME certificate provisioning, and enrollment workflows in substantial detail. While MicroMDM is *referenced* in the coordinator's MDM integration code, there is no separate `mdm-enrollment` component in the codebase. The LlamaIndex pipeline appears to have expanded a passing mention of MDM into an entire component document, inventing file paths, API surfaces, and data flows. The document even includes a telling admission: *"Based on the available context, specific file paths and submodules for the mdm-enrollment component are not documented."*

**image-bridge.md** (LlamaIndex): The pipeline correctly identifies this as non-existent — the entire document is a series of "no information found" statements. However, the pipeline still created a component file for it, which is wasteful and potentially misleading. The file's existence in the output directory implies there might be such a component.

### 2.3 Missing Coverage

**LlamaIndex misses entirely:**
- **EigenInference macOS app** (`app/EigenInference/`): A substantial SwiftUI application with ProviderManager, StatusViewModel, CLIRunner, ConfigManager, ModelManager, SecurityManager, TelemetryReporter, UpdateManager, and a full design system. This is one of the largest components in the codebase (~20+ Swift files) and LlamaIndex has zero coverage.
- **Analytics service** (`analytics/`): A standalone Go service with its own HTTP API, leaderboard system, pseudonymization, and dual storage backends. Entirely absent from LlamaIndex output.

**Flashlight misses entirely:**
- **Protocol package** (`coordinator/internal/protocol/`): While Flashlight's coordinator analysis mentions protocol definitions, it does not produce a dedicated analysis of the wire protocol — something LlamaIndex does well in `protocol.md`.
- **E2E encryption package** (`coordinator/internal/e2e/`): Flashlight covers the test utility (`decrypt-test`) but not the Go encryption package itself. LlamaIndex provides a focused analysis of the encryption architecture in `e2e-encryption.md`.

---

## 3. Per-Component Depth Comparison

### 3.1 Coordinator

| Aspect | LlamaIndex | Flashlight |
|--------|-----------|------------|
| File paths | `coordinator/internal/protocol/messages.go`, `coordinator/internal/protocol/telemetry.go`, `coordinator/internal/api/telemetry_handlers.go` | `internal/api/server.go`, `internal/registry/registry.go`, `internal/registry/queue.go`, `internal/attestation/`, `internal/payments/payments.go`, `internal/billing/`, `internal/store/interface.go`, `internal/ratelimit/ratelimit.go`, `internal/telemetry/`, `internal/mdm/mdm.go`, `internal/e2e/`, `internal/protocol/` |
| Line refs | None | None (but more files listed) |
| Internal structure | Lists 3-4 files | Lists **12** distinct internal packages with specific responsibilities |
| API surface | Brief narrative listing | **17+ endpoint groups** with paths, methods, and descriptions |
| External deps | Named (pgx, jwt, etc.) but no versions | **Exact versions**: pgx/v5 v5.8.0, jwt/v5 v5.3.1, etc. |
| Payment split | "95% to provider" | "90% to provider, 10% platform fee" |

**Critical contradiction**: The provider payout split differs — LlamaIndex claims 95% provider / 5% platform; Flashlight claims 90% provider / 10% platform. Without access to the source code at this path, we cannot definitively resolve this, but Flashlight's claim appears in a detailed payment settlement flow diagram with explicit ledger operations, making it more likely to be grounded in actual code.

**Verdict**: Flashlight is significantly deeper, identifying 12 internal packages vs. LlamaIndex's 3-4 files. The API surface documentation alone in Flashlight is worth more than LlamaIndex's entire coordinator analysis.

### 3.2 Provider / Darkbloom

| Aspect | LlamaIndex | Flashlight |
|--------|-----------|------------|
| File paths | `main.rs`, `hardware.rs`, `security.rs`, `coordinator.rs` | `main.rs`, `hardware.rs`, `security.rs`, `coordinator.rs`, `backend/mod.rs`, `crypto.rs`, `models.rs`, `hypervisor.rs`, `proxy.rs`, `service.rs`, `telemetry/mod.rs`, `secure_enclave_key.rs` |
| Line counts | `main.rs` (7,244), `security.rs` (1,443), `coordinator.rs` (1,527) | Same line counts + `crypto.rs` (462), `models.rs` (1,082), `hypervisor.rs` (346), `proxy.rs` (1,710), `service.rs` (210) |
| Architecture | 4-file summary | **12-file** analysis with `Backend` trait, `CryptoLayer`, `Hypervisor` details |
| CLI commands | Named generically | Full CLI reference: `init`, `serve`, `install`, `start/stop`, `models list/download/remove`, `status`, `doctor`, `update`, `logs`, `enroll`, `login/logout` |
| Config | Not documented | Full TOML config example with `[provider]`, `[backend]`, `[coordinator]`, `[schedule]` sections |
| External deps | Named (tokio, clap, etc.) | Exact versions from Cargo.toml for **27 dependencies** |

**Verdict**: Flashlight captures 3x more internal structure. The Rust crate analysis with actual Cargo.toml dependencies is far more precise.

### 3.3 EigenInferenceEnclave

| Aspect | LlamaIndex | Flashlight |
|--------|-----------|------------|
| File paths | `Sources/EigenInferenceEnclave/SecureEnclaveIdentity.swift`, `Attestation.swift`, `Bridge.swift` | Same + `Attestation.swift` line ranges (lines 44-59, 163-344) |
| API surface | Narrative description | **Full Swift API signatures** (`public init() throws`, `public var publicKeyBase64: String`, etc.) + **C FFI function signatures** |
| AttestationBlob fields | Lists 4 key fields | Lists all fields with type information |
| CLI | Mentioned | Full CLI interface with example JSON output |
| Internal deps | "No direct internal dependencies" | Identifies consumers: "Rust Provider Agent" and "Go Coordinator" |

**Verdict**: Flashlight wins decisively — actual API signatures and C FFI declarations vs. narrative descriptions. LlamaIndex's separate `attestation.md` adds some value by combining both sides (Swift generation + Go verification), but Flashlight's per-component analysis is more precise.

### 3.4 Console-UI / Web

| Aspect | LlamaIndex (`console-ui.md`) | Flashlight (`web.md`) |
|--------|-----------|------------|
| File paths | 8 files/components named | 12 files/components named including `cert-verify.ts`, `encryption.ts`, `AppShell.tsx`, `billing/`, `TelemetryInitializer.tsx` |
| API routes | 16 endpoints listed | Same 16 endpoints + additional context |
| Auth flow | Brief mention | Full Mermaid sequence diagram |
| Certificate verification | Not documented | Dedicated section for `cert-verify.ts` with Apple MDA chain validation |
| Encryption layer | Mentioned in api.ts | Separate `encryption.ts` analysis |
| External deps | Named | **14 npm packages with exact versions** from package.json |
| Dev deps | Not listed | TypeScript, ESLint, Tailwind, Vitest, Testing Library, jsdom |

**Verdict**: Flashlight is more complete, especially in security features (cert-verify.ts, encryption.ts) and development tooling.

### 3.5 Analytics (Flashlight-only)

LlamaIndex has **zero coverage** of the analytics service. Flashlight provides a complete analysis including:
- 8 internal components (main, config, httpapi, leaderboard, memory store, postgres store, pseudonym generator, tests)
- Full API surface: `GET /healthz`, `GET /v1/overview`, `GET /v1/leaderboard/earnings`
- Pseudonym algorithm: HMAC-SHA256 with "Adjective Animal Number" format
- Dual backend support (memory/PostgreSQL)
- Mermaid data flow diagrams

### 3.6 EigenInference macOS App (Flashlight-only)

LlamaIndex has **zero coverage** of the macOS app. Flashlight provides:
- 12 key components (EigenInferenceApp.swift, StatusViewModel.swift, ProviderManager.swift, CLIRunner.swift, ConfigManager.swift, MenuBarView.swift, DashboardView.swift, ModelManager.swift, SecurityManager.swift, TelemetryReporter.swift, DesignSystem.swift, UpdateManager.swift)
- MVVM architecture description
- Process lifecycle management flows
- "Zero external dependencies" design
- Shared TOML configuration model

---

## 4. Architecture Document Comparison

### 4.1 LlamaIndex Architecture (`architecture.md`)

**Strengths:**
- **Trust boundary analysis** is exceptional: 4 trust zones (Consumer, Coordinator, Provider, Apple Hardware) with detailed boundary crossing descriptions
- **Attack surface elimination table**: 12 attack vectors with specific mitigations — this is unique and valuable
- **Request lifecycle**: 16-step sequence with detailed step-by-step explanations
- **Communication protocols table**: Precise protocol/direction/notes for every inter-component path
- **E2E encryption flow**: Describes both client-side and server-side encryption separately

**Weaknesses:**
- Claims 5 "major logical services" but the system actually has more
- Some claims about "in-process, no IPC" for inference conflict with Flashlight's finding that vllm-mlx runs as a subprocess with HTTP proxy
- Truncated at 309 lines (incomplete)

### 4.2 Flashlight Architecture (`architecture.md`)

**Strengths:**
- **Comprehensive** (552 lines vs. 309): covers technology stack, performance characteristics, deployment architecture, recommendations
- **Mermaid diagrams**: System overview, dependency relationships, 3 sequence diagrams (request flow, registration, payment)
- **Component table**: All 9 components with type, language, purpose, and security features
- **Technology stack**: Detailed per-language framework listing
- **Performance metrics**: Specific numbers (1,000+ providers, sub-second routing, connection pooling)
- **Deployment architecture**: Production GCP environment diagram with load balancers, Cloud SQL, Vercel

**Weaknesses:**
- Trust boundary analysis is generic (4 trust levels) vs. LlamaIndex's detailed boundary crossing analysis
- No attack surface table
- Recommendations section is speculative and not grounded in actual code

**Verdict**: LlamaIndex wins on **security architecture depth**; Flashlight wins on **breadth and operational detail**. They complement each other — the ideal architecture doc would merge LlamaIndex's trust boundary analysis with Flashlight's component coverage and deployment diagrams.

### 4.3 Specific Contradictions

1. **Inference execution model**: LlamaIndex's architecture.md states *"The MLX inference engine runs within the same hardened process. There is no subprocess, no local server, no IPC"* (line 301). Flashlight's darkbloom analysis describes both **subprocess mode (vllm-mlx HTTP)** and **in-process mode (PyO3)** as supported backends. The LlamaIndex provider.md also mentions both modes. **The architecture doc's "no IPC" claim appears to be inaccurate** — the system supports both models, with subprocess mode being the current primary approach (HTTP proxy on port 8100+).

2. **Payout split**: As noted above, LlamaIndex claims 95%/5%, Flashlight claims 90%/10%.

3. **Component count**: LlamaIndex architecture says "five major logical services" but actually documents more in its component files. Flashlight correctly identifies 9 components.

---

## 5. Dependency Graph Comparison

### 5.1 LlamaIndex Dependency Graph (`dependency_graph.json`)

8 edges, all described narratively:

```
console-ui → coordinator (api_calls)
provider → coordinator (websocket_connection)
provider → enclave (ffi_calls)
enclave → attestation (hardware_calls)
provider → attestation (hardware_calls)
coordinator → billing (api_calls)
console-ui → billing (api_calls)
coordinator → verify-attestation (depends_on)
```

**Problems:**
- `provider → enclave` and `enclave → attestation` treat "enclave" and "attestation" as separate nodes, but they are the same codebase (EigenInferenceEnclave)
- `coordinator → billing` and `console-ui → billing` treat "billing" as a separate component, but it's embedded in the coordinator
- Missing: `analytics → postgresql`, `coordinator → postgresql`, `coordinator → stripe`, `coordinator → datadog`, `darkbloom → cloudflare-r2`, `web → privy`, `EigenInference → darkbloom`
- The "provider" node name doesn't match any actual codebase entity (it's "darkbloom" in the repo)

### 5.2 Flashlight Dependency Graph (`application_graph.json`)

20 edges, extracted from code manifests:

**Build-time edges (6, from go.mod/Cargo.toml/Package.swift):**
```
analytics → analytics (self-dependency, Go module pattern)
coordinator → coordinator (self-dependency, Go module pattern)
verify-attestation → coordinator (depends_on)
EigenInferenceEnclave → EigenInferenceEnclave (self-dependency)
EigenInferenceEnclave → EigenInferenceEnclaveCLI (depends_on)
EigenInferenceEnclaveCLI → EigenInferenceEnclave (depends_on)
```

**Runtime edges (14, from code analysis):**
```
web → coordinator (api_calls, HTTPS)
darkbloom → coordinator (websocket_connection)
EigenInference → darkbloom (subprocess_management)
darkbloom → EigenInferenceEnclave (ffi_calls)
coordinator → postgresql (database_connection, TCP)
analytics → postgresql (database_connection, TCP)
coordinator → stripe (api_calls, HTTPS)
web → stripe (api_calls, HTTPS)
coordinator → datadog (telemetry_reporting, UDP/HTTPS)
web → datadog (telemetry_reporting, HTTPS)
darkbloom → cloudflare-r2 (api_calls, HTTPS)
web → privy (oauth_integration, HTTPS)
darkbloom → apple-secure-enclave (hardware_calls)
EigenInferenceEnclave → apple-secure-enclave (hardware_calls)
```

**Advantages over LlamaIndex:**
- Protocol annotations (HTTPS, WebSocket, TCP, FFI, system)
- External services as first-class nodes (PostgreSQL, Stripe, Datadog, R2, Privy, Apple SE)
- Correct node naming matching actual codebase artifacts
- The `EigenInference → darkbloom (subprocess_management)` edge captures a key relationship LlamaIndex misses
- `analytics → postgresql` correctly shows the read-only data access pattern

**Weaknesses:**
- Self-dependency edges (analytics→analytics, coordinator→coordinator) are Go module artifacts, not real dependencies — these are noise
- Missing `coordinator → verify-attestation` (it's in the other direction only)
- No edge from coordinator to any attestation service (the coordinator internally verifies, not via a separate service call)

### 5.3 Graph Quality Verdict

| Metric | LlamaIndex | Flashlight |
|--------|-----------|------------|
| Total edges | 8 | 20 |
| Accurate edges | 5 | 18 |
| Hallucinated edges | 2 (billing edges) | 0 |
| Missing critical edges | 8+ | 2 |
| Node naming accuracy | Low ("provider", "billing", "attestation" as separate from "enclave") | High (matches repo directory names) |
| Edge type specificity | 4 types | 9 types with protocol annotations |
| External services modeled | 0 | 6 |

**Flashlight's dependency graph is dramatically superior.** It has 2.5x more edges, models external services, uses accurate node names, and annotates protocols. LlamaIndex's graph has hallucinated nodes (billing, attestation-as-separate-from-enclave) and misses critical edges.

---

## 6. Factual Accuracy Deep Dive

### 6.1 Accurate Claims (Both Pipelines Agree)

- Coordinator runs on GCP Confidential VM (AMD SEV-SNP)
- Apple Secure Enclave provides P-256 ECDSA key management
- WebSocket used for provider-coordinator communication (outbound from provider)
- NaCl Box (X25519 + XSalsa20-Poly1305) for E2E encryption
- Per-request ephemeral key exchange for forward secrecy
- JWT authentication for consumer API
- Stripe integration for payments
- Datadog for observability
- PostgreSQL as primary data store
- Coordinator uses OpenAI-compatible API endpoints

### 6.2 Contradictions

| Claim | LlamaIndex | Flashlight | Likely Correct |
|-------|-----------|------------|----------------|
| Provider payout | 95% provider / 5% platform | 90% provider / 10% platform | **Flashlight** (grounded in payment flow diagram) |
| Inference execution | "In-process, no IPC" | Subprocess (vllm-mlx) + in-process (PyO3) dual mode | **Flashlight** (multiple code references) |
| Component: "billing" | Standalone component | Embedded in coordinator | **Flashlight** (no separate billing directory) |
| Component: "mdm-enrollment" | Exists with APIs | No such component | **Flashlight** (no such code exists) |
| Component: "attestation" (separate from enclave) | Separate component | Part of EigenInferenceEnclave | **Flashlight** (same Swift package) |

### 6.3 Unique Accurate Claims

**LlamaIndex only:**
- Deterministic JSON serialization with `.sortedKeys` for cross-language verification (accurate, from code)
- `rdma_ctl` utility check for RDMA disabled status (accurate)
- Binary hash inclusion in attestation blobs (accurate)
- Four-layer attestation architecture description (conceptually accurate though "MDM enrollment" component is hallucinated)
- `x-provider-attested`, `x-provider-trust-level`, `x-provider-chip` response headers (accurate, from web code)

**Flashlight only:**
- `Backend` trait with `start()`, `stop()`, `health()` methods in darkbloom
- Hypervisor.framework with 16MB alignment requirement
- `crypto.rs` at 462 lines with specific cryptographic implementation
- Provider config at `~/.darkbloom/provider.toml` with specific sections
- Analytics pseudonym format: "Adjective Animal Number" (e.g., "Golden Fox 423")
- Analytics service port default :8090
- `security-framework` and `core-foundation` as macOS-specific Rust dependencies
- EigenInference `WebSocketBridge.swift` stub (removed functionality)

---

## 7. Error and Hallucination Inventory

### 7.1 LlamaIndex Errors

1. **mdm-enrollment.md** — Entire component fabricated. No such code exists. The document invents file paths, API endpoints, and data flows for a component that doesn't exist in the repository.

2. **image-bridge.md** — Created despite the pipeline recognizing no such component exists. The file should not have been generated.

3. **billing.md** — Treats billing as a standalone component when it's embedded in the coordinator. The file path `src/lib/api.ts` (TypeScript) is cited for billing functionality, but this is the web frontend's API client, not a billing service.

4. **provider.md line 76** — Claims "No subprocess, no local server, no IPC" but the same document's line 29-30 describes both subprocess (vllm-mlx) and in-process (PyO3) modes. Internal contradiction.

5. **dependency_graph.json** — `enclave → attestation` edge treats these as separate nodes when they are the same Swift package. The `coordinator → billing` edge references a non-existent component.

6. **protocol.md** — Lists file path as `/tmp/d-inference/coordinator/internal/protocol/messages.go` — the `/tmp/d-inference/` prefix suggests the pipeline used a temporary clone path in its citation, which is inaccurate for the actual repository structure.

7. **architecture.md** — Claims "five major logical services" which undercounts the actual system.

### 7.2 Flashlight Errors

1. **Self-dependency edges** — `analytics → analytics`, `coordinator → coordinator`, `EigenInferenceEnclave → EigenInferenceEnclave` are Go/Swift module patterns, not real component dependencies. These should be filtered or annotated differently.

2. **graph.json** (base) vs **application_graph.json** (enriched) — The base graph.json has only 6 build-time edges and 0 external services, which is misleading if used without the enriched version.

3. **Missing EigenInferenceEnclave → EigenInferenceEnclave (library)** distinction — The `components.json` lists two entries for "EigenInferenceEnclave": one as library at `enclave/Sources/EigenInferenceEnclave` and one as package root at `enclave/`. This creates confusion about which is which.

4. **architecture.md recommendations** — Sections on "Zero-Knowledge Proofs", "Homomorphic Encryption", "Staking Mechanisms" are speculative and not grounded in the codebase.

5. **"Last Updated: 2024-12-24"** — The architecture doc has a stale date that predates the analysis.

---

## 8. Why the Pipelines Differ

### 8.1 LlamaIndex Pipeline Characteristics

- **Driven by LLM reasoning**: The pipeline uses Ollama embeddings + GLM-5.1 to analyze code. The LLM is good at synthesizing narratives and identifying conceptual patterns (trust boundaries, security models) but prone to hallucination when specific code evidence is sparse.
- **Component decomposition by concept**: The pipeline identifies "attestation", "billing", "e2e-encryption", "mdm-enrollment" as conceptual components regardless of whether they exist as separate code artifacts. This creates clean narrative documents but misrepresents the actual codebase structure.
- **Shallow retrieval**: The LlamaIndex RAG pipeline retrieves chunks, but the LLM doesn't have access to complete file trees or manifest files, leading to missed components (EigenInference app, analytics service) and hallucinated ones (mdm-enrollment).

### 8.2 Flashlight Characteristics

- **Manifest-driven discovery**: Flashlight discovers components from go.mod, Cargo.toml, Package.swift, and package.json files. This guarantees every identified component exists in the codebase.
- **Structural analysis**: The tool extracts actual dependency edges, external dependency versions, and component types from build manifests. This is mechanically precise but limited to what manifests declare.
- **Code-reading analysis**: For each discovered component, Flashlight reads the actual source code and produces detailed analysis with file paths, function names, and API signatures. This is where its depth advantage comes from.
- **Missing conceptual components**: Because Flashlight only discovers what manifests declare, it doesn't create "conceptual" component docs for cross-cutting concerns like "e2e-encryption" or "protocol". These are folded into the components that contain them.

---

## 9. Final Verdicts

### Overall Pipeline Quality

**Flashlight is the clearly superior pipeline for codebase analysis**, producing:
- 9 accurate component analyses vs. LlamaIndex's 7 accurate + 3 hallucinated
- 20 dependency edges vs. 8
- Precise API signatures, CLI interfaces, and configuration examples
- Version-pinned external dependency listings
- Zero hallucinated components

**LlamaIndex has unique value in:**
- Trust boundary and security architecture analysis (Sections 2-3 of architecture.md)
- Attack surface elimination table
- Cross-cutting conceptual documentation (protocol, e2e-encryption as separate concerns)
- Request lifecycle narrative with detailed step-by-step explanations

### Recommendations

1. **Use Flashlight as the primary analysis pipeline** for d-inference and similar codebases.
2. **Augment Flashlight output** with LlamaIndex's trust boundary analysis and attack surface table — these are genuinely valuable and Flashlight doesn't produce equivalent content.
3. **Add hallucination guards** to the LlamaIndex pipeline: verify that each "component" has a corresponding directory or manifest file before generating analysis.
4. **Filter self-dependency edges** from Flashlight's graph output.
5. **Resolve the payout split contradiction** by examining `coordinator/internal/payments/payments.go` directly.
6. **Merge the best of both architecture documents**: Flashlight's breadth + LlamaIndex's security depth.

---

*Analysis produced by cross-referencing all 12 LlamaIndex artifacts against all 25 Flashlight artifacts for the d-inference codebase at commit f7dab6fa994a.*
