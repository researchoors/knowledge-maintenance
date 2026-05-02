# Participants and Components

This section lists implementation components discovered from the flashlight service-discovery artifact.

| Component | Kind | Type | Root | Role |
|---|---:|---:|---|---|
| `analytics` | library | go-module | `analytics` | Analytics library providing read-only data access and pseudonymization |
| `analytics` | service | go-module | `analytics/cmd/analytics` | Standalone read-only analytics service for network statistics and earnings leaderboards |
| `coordinator` | library | go-module | `coordinator` | Core coordination library with provider registry, attestation, and payment systems |
| `coordinator` | service | go-module | `coordinator/cmd/coordinator` | Central control plane for routing AI inference requests to provider nodes with hardware attestation |
| `verify-attestation` | service | go-module | `coordinator/cmd/verify-attestation` | Utility service for verifying Apple Secure Enclave attestations |
| `web` | frontend | typescript-package | `console-ui` | Next.js web frontend providing chat interface and provider dashboard with E2E encryption |
| `decrypt-test` | service | rust-crate | `coordinator/internal/e2e/testdata/decrypt` | Test utility for E2E encryption validation |
| `darkbloom` | service | rust-crate | `provider` | EigenInference provider agent for Apple Silicon Macs with hardware-attested security |
| `EigenInference` | frontend | swift-package | `app/EigenInference/Sources/EigenInference` | macOS menu bar application for managing darkbloom provider with native SwiftUI interface |
| `EigenInferenceEnclave` | library | swift-package | `enclave/Sources/EigenInferenceEnclave` | Swift package providing Secure Enclave attestation and signing capabilities |
| `EigenInferenceEnclaveCLI` | cli | swift-package | `enclave/Sources/EigenInferenceEnclaveCLI` | CLI tool for Secure Enclave operations and diagnostics |
| `EigenInferenceEnclave` | library | swift-package | `enclave` | Swift package root providing Secure Enclave attestation and signing capabilities |

## Component requirements

- <!-- req: system.role.coordinator; source: artifacts/d-inference/service_discovery/components.json#L30-L87 --> Coordinator components MUST be treated as control-plane components for routing, attestation integration, and accounting.
- <!-- req: system.role.provider; source: artifacts/d-inference/service_discovery/components.json#L193-L315 --> The `darkbloom` provider component MUST be treated as the provider-side runtime for Apple Silicon inference capacity.
- <!-- req: system.role.enclave; source: artifacts/d-inference/service_discovery/components.json#L330-L339 --> The `EigenInferenceEnclave` components MUST be treated as the provider-side hardware-attestation and signing boundary.
- <!-- req: system.role.web; source: artifacts/d-inference/service_discovery/components.json#L103-L169 --> The `web` component SHOULD be treated as the user-facing interface, not as a source of provider attestation truth.
