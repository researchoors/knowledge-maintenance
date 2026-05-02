# Open Questions

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
