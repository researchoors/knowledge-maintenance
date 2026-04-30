## Overview

The coordinator is the central control plane for the d-inference network, written in Go and deployed on GCP Confidential VMs (AMD SEV-SNP). It serves as the trust and routing layer between consumers submitting OpenAI-compatible inference requests and hardened provider agents running on Apple Silicon, managing WebSocket connections to providers, HTTP API endpoints for consumers, billing via Stripe, attestation verification, and encrypted request forwarding.

## Architecture

- **`coordinator/internal/protocol/messages.go`**: Defines the wire protocol message types shared between coordinator and provider agents. Implements a tagged union pattern using JSON with a "type" field discriminator. Contains message type constants for both directions (Provider→Coordinator: `register`, `heartbeat`, `inference_response_chunk`, `inference_complete`, `inference_error`, `attestation_response`; Coordinator→Provider: `inference_request`, `cancel`, `attestation_challenge`, `runtime_status`) and hardware/model descriptor structs like `CPUCores`.

- **`coordinator/internal/protocol/telemetry.go`**: Defines telemetry wire types that must stay in sync with `provider/src/telemetry/event.rs` and `console-ui/src/lib/telemetry-types.ts`.

- **`coordinator/internal/api/telemetry_handlers.go`**: Contains the field allowlist that serves as the privacy backstop — never adds prompt/completion fields.

- **`coordinator/eigeninference-coordinator`** and **`coordinator/eigeninference-coordinator-linux`**: Compiled binaries (should not be committed to git, 15MB+ each).

- **`coordinator_lib`**: Shared library dependency used by the coordinator and also by `verify-attestation`.

## Dependencies

- **EigenInferenceEnclave / verify-attestation**: The `verify-attestation` service depends on `coordinator_lib` for attestation verification logic, validating Apple MDA certificate chains.

- **analytics**: Read-only access to the same PostgreSQL database for business intelligence without impacting coordinator performance. Intentionally isolated with separate DB credentials and SELECT-only privileges.

- **darkbloom (provider agent)**: Connects to coordinator via WebSocket (outbound from provider). Coordinator dispatches encrypted inference requests and receives registration, heartbeats, response chunks, and attestation responses.

- **web (console-ui)**: React frontend consuming coordinator REST API for user dashboard, provider management, and billing interfaces. Telemetry types must stay in sync.

- **PostgreSQL**: Primary data store for API keys, usage records, balance ledger, provider fleet state, and user accounts. Coordinator uses in-memory store by default; Postgres store exists but is not yet used in production.

- **Stripe**: Payment processing — Checkout for consumer deposits, Connect Express for provider withdrawals.

- **GCP Confidential VM (AMD SEV-SNP)**: Hardware-encrypted execution environment providing memory encryption and integrity protection; the coordinator's trust model depends on this.

- **Datadog**: Observability via DogStatsD (metrics), Logs API, and APM agent (traces).

- **MicroMDM**: Independent provider verification validating Apple Business Manager enrollment and device security policies.

- **step-ca**: Certificate Authority for ACME device-attest-01 protocol, issuing client certificates bound to provider Secure Enclave keys.

- **Tempo / Ethereum / Solana**: Blockchain networks for pathUSD payments, provider wallet settlements, and crypto deposits.

## API Surface

- **HTTPS API (Consumer-facing)**: OpenAI-compatible inference endpoints, balance management, user accounts, billing interfaces consumed by SDK clients, console UI, and curl.

- **WebSocket API (Provider-facing)**: Outbound connections from providers; coordinator sends `inference_request`, `cancel`, `attestation_challenge`, `runtime_status`; receives `register`, `heartbeat`, `inference_accepted`, `inference_response_chunk`, `inference_complete`, `inference_error`, `attestation_response`.

- **Protocol types**: `Message` struct with `Body` (plain JSON) or `EncryptedBody` (X25519/NaCl-box encrypted payload). The coordinator decrypts sender-sealed requests inside its Confidential VM for routing, then re-encrypts to the provider before dispatch.

- **Telemetry API**: Field-allowlisted telemetry endpoints with privacy backstop preventing prompt/completion data exposure.

## Security Considerations

- **Confidential VM isolation**: Runs on GCP AMD SEV-SNP providing hardware-level memory encryption and integrity protection.

- **End-to-end encryption**: Inference requests are encrypted with provider X25519 public keys. The coordinator can decrypt sender-sealed requests inside the Confidential VM for routing but re-encrypts before dispatch — providers are the only ones who can decrypt their assigned requests.

- **JWT authentication**: Used for consumer API access.

- **Rate limiting**: Applied to API endpoints.

- **Attestation verification**: Provider attestation via Secure Enclave challenge-response. The coordinator issues `attestation_challenge` messages and validates `attestation_response` using Apple MDA certificate chains. Attestation field uses `json.RawMessage` to preserve exact bytes for signature verification.

- **MDM-based independent verification**: MicroMDM validates device enrollment and security policies outside of provider self-attestation.

- **Certificate-bound authentication**: step-ca issues client certificates bound to Secure Enclave keys for hardware-verified provider authentication.

- **Telemetry privacy**: Strict field allowlist in `telemetry_handlers.go` prevents prompt/completion data from being exposed.

- **Protocol sync requirement**: Protocol changes require updating both `provider/src/protocol.rs` (Rust) AND `coordinator/internal/protocol/messages.go` (Go) — they must stay in sync.

## Data Flow

1. **Consumer request entry**: A consumer sends an OpenAI-compatible HTTPS request to the coordinator API, authenticated via JWT.

2. **Request decryption and routing**: The coordinator decrypts the sender-sealed request inside its Confidential VM to determine routing (model selection, provider availability).

3. **Request re-encryption and dispatch**: The coordinator re-encrypts the request using the target provider's X25519 public key (NaCl box) and sends it as an `inference_request` WebSocket message with the payload in `EncryptedBody`.

4. **Provider processing**: The hardened provider process (darkbloom) decrypts the request using its Secure Enclave-managed key, runs inference via vllm-mlx on Apple Silicon GPU, and streams back `inference_response_chunk` messages followed by `inference_complete` (or `inference_error`).

5. **Response relay**: The coordinator relays response chunks back to the consumer over HTTPS.

6. **Billing settlement**: Usage is recorded in PostgreSQL; provider earnings are settled via Tempo/Ethereum/Solana blockchains and Stripe Connect Express for withdrawals.

7. **Ongoing attestation**: The coordinator periodically issues `attestation_challenge` messages to providers, validating responses against Apple MDA certificate chains and MDM enrollment status to ensure security posture hasn't been tampered with.