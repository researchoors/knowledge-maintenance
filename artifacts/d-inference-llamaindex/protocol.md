## Overview

The `protocol` package defines the wire protocol message types shared between the coordinator and provider agents over WebSocket connections. All messages are JSON-encoded with a `"type"` field used as a discriminator to determine which concrete struct to unmarshal into, implementing a simple tagged union pattern. It serves as the foundational shared contract governing every communication between the two sides of the system.

## Architecture

**`/tmp/d-inference/coordinator/internal/protocol/messages.go`** — The sole file in this package, containing:

- **Message type constants**: String discriminators for all message directions (Provider→Coordinator: `register`, `heartbeat`, `inference_accepted`, `inference_response_chunk`, `inference_complete`, `inference_error`, `attestation_response`; Coordinator→Provider: `inference_request`, `cancel`, `attestation_challenge`, `runtime_status`)
- **Hardware/metrics descriptors**: `CPUCores`, `SystemMetrics`, `HeartbeatStats`
- **Provider→Coordinator message structs**: `InferenceAcceptedMessage`, `InferenceResponseChunkMessage`, `InferenceCompleteMessage`, `InferenceErrorMessage`
- **Coordinator→Provider message structs**: `ChatMessage`, `InferenceRequestBody`, `InferenceRequestMessage`, `CancelMessage`, `AttestationChallengeMessage`
- **Cryptographic carrier type**: `EncryptedPayload` for NaCl Box–encrypted bodies

## Dependencies

- **Standard library only** (`encoding/json`, `fmt`): The package is intentionally self-contained with no internal d-inference dependencies, making it safe for both the coordinator and provider to import without coupling.
- **Depended upon by**: The coordinator service, the provider agent (Rust side via JSON interop), and the store package (which deliberately mirrors certain types like `TelemetryEventRecord` to avoid importing protocol directly and stay free of protocol-layer coupling).

## API Surface

| Category | Exports |
|---|---|
| **Constants** | `TypeRegister`, `TypeHeartbeat`, `TypeInferenceAccepted`, `TypeInferenceResponseChunk`, `TypeInferenceComplete`, `TypeInferenceError`, `TypeAttestationResponse`, `TypeInferenceRequest`, `TypeCancel`, `TypeAttestationChallenge`, `TypeRuntimeStatus` |
| **Message structs** | `InferenceAcceptedMessage`, `InferenceResponseChunkMessage`, `InferenceCompleteMessage`, `InferenceErrorMessage`, `InferenceRequestMessage`, `CancelMessage`, `AttestationChallengeMessage` |
| **Supporting types** | `CPUCores`, `SystemMetrics`, `HeartbeatStats`, `ChatMessage`, `InferenceRequestBody`, `UsageInfo`, `EncryptedPayload` |

## Security Considerations

- **End-to-end encryption via NaCl Box (X25519)**: `InferenceRequestMessage` carries either a plaintext `Body` or an `EncryptedBody` containing an ephemeral sender public key and `nonce || ciphertext`. The coordinator cannot decrypt past requests because it uses per-request ephemeral key exchange. Similarly, `InferenceResponseChunkMessage` supports `EncryptedData` for encrypted response streaming.
- **Secure Enclave attestation**: `AttestationChallengeMessage` / `TypeAttestationResponse` implement periodic challenge-response to verify the provider still holds its private key. `json.RawMessage` is used for the `Attestation` field to preserve exact bytes for signature verification.
- **Response integrity**: `InferenceCompleteMessage` includes `SESignature` (Secure Enclave–signed response hash) and `ResponseHash` (SHA-256 of response data), binding the output to the attested hardware.
- **Inference acceptance window**: `InferenceAcceptedMessage` signals the provider has committed to the request, allowing the coordinator to extend the timeout while still permitting retry if the provider fails before the first chunk.

## Data Flow

**Inference request lifecycle:**

1. **Coordinator → Provider**: `InferenceRequestMessage` dispatched with a `RequestID`, either plaintext `Body` (model, messages, stream flag, max_tokens, temperature, endpoint) or `EncryptedBody` (NaCl Box).
2. **Provider → Coordinator**: `InferenceAcceptedMessage` acknowledges acceptance; coordinator extends the wait window to the full inference timeout but may retry if the provider fails before the first chunk.
3. **Provider → Coordinator**: One or more `InferenceResponseChunkMessage` payloads stream back, each carrying `Data` (plaintext SSE chunk) or `EncryptedData` (encrypted chunk).
4. **Provider → Coordinator**: `InferenceCompleteMessage` signals generation is finished, including `UsageInfo` (prompt/completion token counts), `SESignature`, and `ResponseHash`.
5. **Error path**: `InferenceErrorMessage` is sent with an error string and status code.

**Auxiliary flows:**

- **Cancellation**: Coordinator sends `CancelMessage` with the target `RequestID`.
- **Attestation**: Coordinator sends `AttestationChallengeMessage`; provider responds with `TypeAttestationResponse` proving continued key possession and security posture integrity.