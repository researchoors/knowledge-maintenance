# Protocol

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

- <!-- req: runtime.provider; source: artifacts/d-inference/service_analyses/darkbloom.md#L210-L274 --> Provider runtimes expose registration, heartbeat, inference lifecycle, error, cancellation, and attestation-response behavior over their coordinator protocol surface.
- <!-- req: protocol.provider-registration; source: artifacts/d-inference/architecture_docs/architecture.md#L278-L312 --> A provider MUST complete registration and trust establishment before it is eligible for routed inference work.

## Consumer inference flow

- <!-- req: protocol.consumer-flow; source: artifacts/d-inference/architecture_docs/architecture.md#L251-L276 --> A consumer inference request flows through the web/API surface to the coordinator, from the coordinator to an assigned provider, and back as streamed response chunks.
- <!-- req: security.crypto; source: artifacts/d-inference/service_analyses/darkbloom.md#L48-L52 --> Inference payload handling MUST preserve the cryptographic boundary described by the provider cryptography layer when encrypted request mode is used.

## Settlement flow

- <!-- req: protocol.payment-settlement; source: artifacts/d-inference/architecture_docs/architecture.md#L314-L338 --> The coordinator records payment settlement state after inference completion and provider withdrawal events.

## Open schema gaps

The artifacts identify message names and flows, but they do not yet provide complete wire schemas for all provider
messages. Those schemas should be added as explicit protocol tables once source artifacts contain enough detail.
