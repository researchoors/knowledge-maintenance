# D-Inference System Architecture Document

## 1. System Topology

### Major Services and Communication Paths

The system comprises five major logical services connected through specific protocols and trust boundaries:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONSUMER LAYER                               │
│  ┌──────────────┐                                                   │
│  │  console-ui  │  TypeScript web frontend                          │
│  │   (web/)     │  E2E encryption, client-side cert verification    │
│  └──────┬───────┘                                                   │
│         │ HTTPS API (OpenAI-compatible)                             │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TRUST & COORDINATION LAYER                       │
│  ┌──────────────┐   ┌─────────────┐   ┌──────────────┐            │
│  │ coordinator  │──▶│ PostgreSQL  │   │   analytics  │            │
│  │  (Go svc)    │   │             │◀──│   (Go svc)   │            │
│  └──────┬───────┘   └─────────────┘   └──────────────┘            │
│         │          ┌─────────────┐   ┌──────────────┐              │
│         ├─────────▶│   Stripe    │   │   Datadog    │              │
│         │          └─────────────┘   └──────────────┘              │
│         │          ┌─────────────────────────────┐                 │
│         ├─────────▶│ verify-attestation (Go svc)  │                │
│         │          └─────────────────────────────┘                 │
└─────────┼──────────────────────────────────────────────────────────┘
          │ WebSocket (outbound from provider)
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       PROVIDER LAYER                                │
│  ┌──────────────────┐     ┌───────────────────┐                    │
│  │ EigenInference   │────▶│    darkbloom      │                    │
│  │ (Swift macOS app)│     │ (Rust provider    │                    │
│  │  app/EigenInference/   │  agent)           │                    │
│  └──────────────────┘     └────────┬──────────┘                    │
│                                    │ FFI (@_cdecl)                 │
│                                    ▼                               │
│                           ┌───────────────────┐                    │
│                           │ EigenInference    │                    │
│                           │ Enclave (Swift)   │                    │
│                           │ enclave/          │                    │
│                           └────────┬──────────┘                    │
│                                    │                               │
│                                    ▼                               │
│                           ┌───────────────────┐                    │
│                           │  Apple Secure     │                    │
│                           │  Enclave (HW)     │                    │
│                           └───────────────────┘                    │
│                                                                     │
│  ┌──────────────────┐                                               │
│  │  MLX / vllm-mlx  │  Inference engine (in-process)              │
│  └──────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Communication Protocols

| Path | Protocol | Direction | Notes |
|------|----------|-----------|-------|
| console-ui → coordinator | HTTPS REST API | Inbound to coordinator | OpenAI-compatible chat completion endpoints |
| coordinator → PostgreSQL | SQL (read/write) | Outbound | Primary data store for registry, billing, sessions |
| analytics → PostgreSQL | SQL (read-only) | Outbound | Pseudonymized statistics only |
| darkbloom → coordinator | WebSocket | **Outbound from provider** | No port forwarding required; NAT/firewall traversal |
| EigenInference → darkbloom | subprocess | Local | Auto-restart managed by Swift app |
| darkbloom → EigenInferenceEnclave | C FFI (`@_cdecl`) | Local in-process | Key operations, attestation blob signing |
| EigenInferenceEnclave → Secure Enclave | Hardware bus | On-chip | P-256 key generation/storage, non-extractable |
| coordinator → Stripe | HTTPS API | Outbound | Payment processing |
| coordinator → Datadog | HTTPS API | Outbound | Monitoring/observability |
| coordinator → Cloudflare R2 | HTTPS | Outbound | CDN for model artifacts |
| coordinator → Apple Services | HTTPS | Outbound | MDA certificate chain validation |

### Component Details

**coordinator** (`coordinator/`, Go)
- Central routing and trust layer
- Runs in Confidential VM
- JWT authentication, rate limiting
- Depends on: `coordinator_lib`

**darkbloom** (provider agent, Rust)
- Hardened inference agent with hypervisor isolation
- Single process: security module + inference engine + crypto module
- Depends on: `EigenInferenceEnclave` via FFI

**EigenInference** (`app/EigenInference/`, Swift/SwiftUI)
- macOS menu bar app (no dock icon)
- Idle detection via `CGEventSource` (pauses serving when user active)
- Provider subprocess management with auto-restart
- Model discovery from HuggingFace cache
- Dashboard: hardware info, session stats, earnings
- Settings: coordinator URL, API key, availability schedule

**EigenInferenceEnclave** (`enclave/`, Swift)
- Hardware-bound cryptographic identity
- P-256 key generation/storage in Apple Secure Enclave (non-extractable)
- Signed attestation blobs containing: chip info, SIP status, SecureBoot status, SE status, binary hash
- C FFI bridge for Rust integration
- CLI tool: `eigeninference-enclave attest [--encryption-key <b64>] [--binary-hash <hex>]`

**console-ui** (`web/`, TypeScript)
- Consumer/provider web interface
- Client-side E2E encryption
- Client-side certificate verification

---

## 2. Trust Boundaries

### Boundary Map

```
TRUST ZONE A          TRUST ZONE B           TRUST ZONE C
(Consumer)            (Coordinator)          (Provider)
                       Confidential VM        Hardened Process
┌──────────┐         ┌──────────────┐       ┌──────────────────┐
│          │  HTTPS  │              │  WSS   │                  │
│  Client  │────────▶│ Coordinator  │───────▶│  Darkbloom       │
│          │  TLS    │              │  TLS   │  (Rust agent)    │
└──────────┘         └──────────────┘       │                  │
                                              │    ┌──────────┐ │
                                              │    │ Secure   │ │
                                              │    │ Enclave  │ │
                                              │    │ (HW)     │ │
                                              │    └──────────┘ │
                                              └──────────────────┘
                                                     TRUST ZONE D
                                                     (Apple Hardware)
```

### Trust Boundary Crossings and Cryptographic Protections

#### Boundary 1: Consumer → Coordinator (Network)

| Property | Detail |
|----------|--------|
| **Protocol** | HTTPS (TLS 1.3) |
| **Authentication** | JWT tokens |
| **Data exposure** | Coordinator sees plaintext request metadata (model, tokens) but **not** payload content when E2E encryption is used |
| **Cryptographic protection** | Per-request ephemeral key exchange (X25519); coordinator encrypts with provider's public key but cannot decrypt past requests |

The coordinator encrypts inference request payloads using per-request ephemeral key exchange such that the coordinator does not retain the ability to decrypt past requests.

#### Boundary 2: Coordinator → Provider (Network)

| Property | Detail |
|----------|--------|
| **Protocol** | WebSocket over TLS (outbound from provider) |
| **Authentication** | Provider authenticates via attestation-backed identity |
| **Data exposure** | Payloads are already encrypted with provider's X25519 public key |
| **Cryptographic protection** | End-to-end encryption; coordinator is a routing relay, not a decryption intermediary |

#### Boundary 3: Provider Process → Secure Enclave (Hardware/Process)

| Property | Detail |
|----------|--------|
| **Protocol** | Apple Secure Enclave coprocessor interface |
| **Authentication** | Hardware-bound; keys never leave the enclave |
| **Data exposure** | Only signing requests and key generation requests cross this boundary |
| **Cryptographic protection** | P-256 keys are non-extractable; attestation blobs signed by Secure Enclave |

#### Boundary 4: Provider Process → Operating System (Process)

| Property | Detail |
|----------|--------|
| **Mechanism** | Hardened Runtime + PT_DENY_ATTACH |
| **Protection** | Kernel denies `task_for_pid`, debugger attachment, Instruments profiling |
| **Code signing** | Binary signed with Hardened Runtime, WITHOUT `com.apple.security.get-task-allow` |

### Attack Surface Elimination at Trust Boundaries

| Attack Vector | Blocked By | Boundary |
|---------------|-----------|----------|
| Debugger attachment (lldb, dtrace) | `PT_DENY_ATTACH` + Hardened Runtime | Process → OS |
| Read process memory | Hardened Runtime (kernel denies `task_for_pid`) | Process → OS |
| Sniff IPC/network | No IPC — inference is in-process | Process internal |
| Modify the binary | Code signing + SIP | OS → Disk |
| Replace with fake binary | Binary hash in attestation — coordinator verifies | Network → Coordinator |
| Inject malicious Python pkg | Python path locked to signed bundle | Process → OS |
| Load kernel extension | SIP blocks unsigned kexts | OS → Kernel |
| Modify kernel at runtime | KIP (hardware-enforced) | Hardware → Kernel |
| Disable SIP | Requires reboot → kills process → data gone | OS → Hardware |
| Read `/dev/mem` | Doesn't exist on Apple Silicon | Process → OS |
| DMA attack | IOMMU default-deny | Hardware → Memory |
| Physical memory probing | Soldered LPDDR5x into SoC die (lab-grade only) | Physical |

**Residual threat**: Physical memory probing of LPDDR5x soldered into the SoC package — the same threat model accepted by Apple's Private Cloud Compute.

---

## 3. Request Lifecycle

### Complete Chat Completion Request Flow

```
Consumer          console-ui         Coordinator          darkbloom          Secure Enclave
   │                  │                  │                    │                    │
   │  1. User types   │                  │                    │                    │
   │  prompt          │                  │                    │                    │
   │─────────────────▶│                  │                    │                    │
   │                  │                  │                    │                    │
   │                  │ 2. Client-side   │                    │                    │
   │                  │ E2E encryption   │                    │                    │
   │                  │ (X25519 key      │                    │                    │
   │                  │  exchange with   │                    │                    │
   │                  │  provider)       │                    │                    │
   │                  │                  │                    │                    │
   │                  │ 3. HTTPS POST    │                    │                    │
   │                  │ /v1/chat/        │                    │                    │
   │                  │ completions      │                    │                    │
   │                  │─────────────────▶│                    │                    │
   │                  │                  │                    │                    │
   │                  │                  │ 4. Authenticate    │                    │
   │                  │                  │ JWT token          │                    │
   │                  │                  │                    │                    │
   │                  │                  │ 5. Rate limit      │                    │
   │                  │                  │ check              │                    │
   │                  │                  │                    │                    │
   │                  │                  │ 6. Multi-factor    │                    │
   │                  │                  │ scoring algorithm  │                    │
   │                  │                  │ to select provider │                    │
   │                  │                  │ (6-factor composite│                    │
   │                  │                  │  scoring function) │                    │
   │                  │                  │                    │                    │
   │                  │                  │ 7. Encrypt payload │                    │
   │                  │                  │ with provider's    │                    │
   │                  │                  │ X25519 public key  │                    │
   │                  │                  │ (per-request       │                    │
   │                  │                  │  ephemeral key     │                    │
   │                  │                  │  exchange)         │                    │
   │                  │                  │                    │                    │
   │                  │                  │ 8. Route encrypted │                    │
   │                  │                  │ request via        │                    │
   │                  │                  │ WebSocket          │                    │
   │                  │                  │───────────────────▶│                    │
   │                  │                  │                    │                    │
   │                  │                  │                    │ 9. Verify          │
   │                  │                  │                    │ attestation        │
   │                  │                  │                    │ status is valid    │
   │                  │                  │                    │                    │
   │                  │                  │                    │ 10. Decrypt        │
   │                  │                  │                    │ request payload    │
   │                  │                  │                    │ using private key  │
   │                  │                  │                    │ (in protected      │
   │                  │                  │                    │  memory)           │
   │                  │                  │                    │                    │
   │                  │                  │                    │ 11. Execute        │
   │                  │                  │                    │ inference via      │
   │                  │                  │                    │ vllm-mlx/MLX      │
   │                  │                  │                    │ (in-process,       │
   │                  │                  │                    │  no IPC)           │
   │                  │                  │                    │                    │
   │                  │                  │                    │ 12. Encrypt        │
   │                  │                  │                    │ response with      │
   │                  │                  │                    │ consumer's key     │
   │                  │                  │                    │                    │
   │                  │                  │ 13. Encrypted      │                    │
   │                  │                  │ response via       │                    │
   │                  │                  │ WebSocket          │                    │
   │                  │                  │◀───────────────────│                    │
   │                  │                  │                    │                    │
   │                  │ 14. HTTPS        │                    │                    │
   │                  │ response         │                    │                    │
   │                  │◀─────────────────│                    │                    │
   │                  │                  │                    │                    │
   │                  │ 15. Client-side  │                    │                    │
   │                  │ decrypt          │                    │                    │
   │                  │                  │                    │                    │
   │  16. Display     │                  │                    │                    │
   │  response        │                  │                    │                    │
   │◀─────────────────│                  │                    │                    │
```

### Key Steps in Detail

**Step 2 — Client-side E2E Encryption:**
The console-ui performs X25519 key exchange with the target provider's public key. The request payload is encrypted before leaving the consumer's browser.

**Step 6 — Provider Selection (Multi-Factor Scoring):**
The coordinator uses a six-factor composite scoring function with real-time hardware telemetry inputs to select the optimal provider. Factors include:
- Capabilities (model support, memory)
- Trust status (attestation validity)
- Real-time health metrics
- Current load
- Network latency
- Economic factors (pricing)

**Step 7 — Per-Request Ephemeral Key Exchange:**
The coordinator encrypts the inference request payload using per-request ephemeral key exchange. This ensures the coordinator cannot decrypt past requests (forward secrecy).

**Step 10 — Decryption in Protected Memory:**
The darkbloom agent decrypts the request payload within the hardened process. The private key is managed through the Secure Enclave FFI bridge.

**Step 11 — In-Process Inference:**
The MLX inference engine runs within the same hardened process. There is no subprocess, no local server, no IPC. The Python inference engine is accessed via FFI bridge within the single protected process.

**Cancellation Propagation:**
If the consumer cancels the request, the cancellation propagates through the coordinator to the provider via the WebSocket connection, terminating inference execution.

### Response Fields

The response includes EigenInference-specific fields:
- `provider_attested` (bool) — whether the provider's attestation was verified
- `provider_trust_level` (string) — the trust level of the