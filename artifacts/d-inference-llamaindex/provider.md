## Overview

The darkbloom component is a sophisticated provider agent written in Rust that serves as the local inference runtime for Apple Silicon Macs in the EigenInference distributed inference network. It bridges the global coordinator and local hardware, managing ML model execution with enterprise-grade security features including kernel-level debugger denial, Secure Enclave attestation, and hypervisor-isolated memory protection. It runs as a hardened single process with no inter-process communication paths, ensuring inference data cannot be observed by the machine owner.

## Architecture

Key submodules/files and their responsibilities:

- **`main.rs`** (7,244 lines) — CLI command handler and application bootstrapping. Handles command parsing, hardware detection initialization, security initialization, and coordinates all subsystems. Covers installation, serving, and model management commands.

- **`hardware.rs`** — Apple Silicon capability detection and system metrics collection. Detects memory/GPU capabilities, monitors thermal status, and collects performance metrics. Exposes `HardwareInfo` and `SystemMetrics` structs that are reported to the coordinator for job routing decisions.

- **`security.rs`** (1,443 lines) — Runtime hardening and threat protection. Implements PT_DENY_ATTACH (kernel-level debugger denial), SIP verification, memory wiping for sensitive data, core dump disabling, and Secure Enclave integration. Called at startup and before each inference request.

- **`coordinator.rs`** (1,527 lines) — WebSocket connection management to the distributed coordinator. Handles registration, heartbeat transmission, attestation challenge-response, and job routing. Receives inference jobs and reports capacity/health status back to the coordinator.

The architecture follows a **multi-layered service pattern** with:
1. Hardened Runtime Security (PT_DENY_ATTACH, SIP, Secure Enclave)
2. Hypervisor Isolation (Apple Hypervisor.framework for memory isolation of inference workloads)
3. Multi-Backend Support (subprocess vllm-mlx and in-process PyO3 inference engines)
4. Distributed Coordination (WebSocket-based communication with outbound-only connections)

## Dependencies

- **EigenInferenceEnclave (Swift framework)** — The provider depends on this Secure Enclave component for cryptographic operations: key generation (X25519), signing, verification, and attestation blob generation. The provider calls into this via FFI bridge (`Bridge.swift`) for Secure Enclave challenge-response attestation and hardware identity verification.

- **Coordinator service (Go)** — WebSocket communication dependency for job routing, registration, heartbeats, and attestation challenges. The provider maintains an outbound-only WebSocket connection, eliminating the need for port forwarding.

- **vllm-mlx / MLX inference engine** — The actual ML inference execution backend. The provider supports both subprocess mode (vllm-mlx) and in-process mode (PyO3) for running models on Apple Silicon GPU via Metal.

- **Cloudflare R2 CDN** — Model storage and distribution; the provider fetches verified models from the curated catalog stored on R2.

## API Surface

**WebSocket Messages (Provider → Coordinator):**
- `register` — Registration payload with hardware capabilities, trust status, and public key
- `heartbeat` — Periodic health/capacity status updates including system metrics
- `inference_accepted` — Acknowledgment that an inference request has been received and will be processed
- `inference_response_chunk` — Streaming response chunks sent during inference execution
- `inference_complete` — Final inference result marking request completion
- `inference_error` — Error reporting for failed inference requests
- `attestation_response` — Cryptographic attestation blob (Secure Enclave signed) responding to coordinator challenges

**WebSocket Messages (Coordinator → Provider):**
- `inference_request` — Encrypted inference payload (X25519/NaCl-box encrypted)
- `cancel` — Request cancellation
- `attestation_challenge` — Periodic attestation challenge requiring Secure Enclave response
- `runtime_status` — Runtime status queries

**Exposed Types:**
- `HardwareInfo` — Struct describing Apple Silicon capabilities (CPU cores, memory, GPU)
- `SystemMetrics` — Real-time system metrics (memory usage, GPU utilization, thermal status)
- `CPUCores` — CPU core layout descriptor (total, performance, efficiency cores)

**CLI Commands:**
- Installation, serving, and model management commands exposed via `main.rs`

## Security Considerations

1. **PT_DENY_ATTACH** — Kernel-level debugger attachment denial; prevents any debugging tool from observing process memory or execution state.

2. **SIP Verification** — System Integrity Protection checking; disabling SIP requires a reboot that terminates the process, making protections provably immutable for the process lifetime.

3. **Secure Enclave Integration** — Cryptographic attestation with hardware-signed blobs containing system integrity status, hardware identity, and a hash of the running binary. Four-layer attestation architecture: Secure Enclave signatures, MDM-based independent verification, Apple Managed Device Attestation with Apple-signed certificate chains, and periodic challenge-response.

4. **Hardened Runtime** — Blocks memory-reading APIs that could expose inference data.

5. **Memory Wiping** — Sensitive data (inference inputs/outputs, decryption keys) is wiped from memory after use.

6. **Core Dump Disable** — Prevents memory content leakage through crash dumps.

7. **Hypervisor Isolation** — Apple's Hypervisor.framework provides memory isolation for inference workloads, creating a separate protected memory domain.

8. **X25519/NaCl-box Encryption** — Per-request ephemeral key exchange for request/response encryption with forward secrecy. The coordinator encrypts requests with the provider's X25519 public key; only the hardened provider process can decrypt.

9. **In-Process Execution** — No subprocess, no local server, no IPC channels — eliminates all software paths through which inference data could be observed by the machine owner.

10. **Outbound-Only WebSocket** — Provider connects outbound to coordinator, no inbound ports exposed, reducing network attack surface.

## Data Flow

**Request flow (entry to exit):**

1. **Consumer** sends inference request via HTTPS (OpenAI-compatible API) to the Coordinator.

2. **Coordinator** (in Confidential VM) decrypts sender-sealed request for routing, then re-encrypts the request payload using the provider's X25519 public key with per-request ephemeral key exchange.

3. **Coordinator** sends `inference_request` message via WebSocket to the provider's `coordinator.rs` module.

4. **Provider's coordinator.rs** receives the WebSocket message and routes it internally.

5. **Security module** (`security.rs`) verifies runtime integrity before processing — checks SIP status, confirms Hardened Runtime protections are active, validates no debugger attachment.

6. **Provider** decrypts the request payload using its X25519 private key (protected within the hardened process/Secure Enclave context).

7. **Request** is routed to the inference engine — either subprocess mode (vllm-mlx) or in-process mode (PyO3), with in-process being the preferred secure path.

8. **Inference execution** occurs on Apple Silicon GPU via Metal/MLX, within hypervisor-isolated memory.

9. **Response chunks** are generated and sent back via `inference_response_chunk` WebSocket messages, streaming tokens to the coordinator.

10. **Final response** is sent via `inference_complete` message, marking request fulfillment.

11. **Memory wiping** — Inference inputs, outputs, and intermediate data are wiped from process memory after completion.

12. **Periodic attestation** — Throughout operation, the coordinator sends `attestation_challenge` messages; the provider responds with `attestation_response` containing Secure Enclave-signed attestation blobs verifying continued security posture.

The residual threat model is physical probing of memory chips soldered into the SoC package — the same threat model accepted by Apple's Private Cloud Compute.