# Components

| Component | Kind | Language | Description |
|-----------|------|----------|-------------|
| [analytics](./service/analytics.md) | service | Go Module | Standalone read-only analytics service for network statistics and earnings leaderboards |
| [coordinator](./service/coordinator.md) | service | Go Module | Central control plane for routing AI inference requests to provider nodes with hardware attestation |
| [darkbloom](./service/darkbloom.md) | service | Rust Crate | EigenInference provider agent for Apple Silicon Macs with hardware-attested security |
| [decrypt-test](./service/decrypt-test.md) | service | Rust Crate | Test utility for E2E encryption validation |
| [verify-attestation](./service/verify-attestation.md) | service | Go Module | Utility service for verifying Apple Secure Enclave attestations |
| [EigenInference](./frontend/eigeninference.md) | frontend | Swift Package | macOS menu bar application for managing darkbloom provider with native SwiftUI interface |
| [web](./frontend/web.md) | frontend | Typescript Package | Next.js web frontend providing chat interface and provider dashboard with E2E encryption |
| [EigenInferenceEnclave](./library/eigeninferenceenclave.md) | library | Swift Package | Swift package providing Secure Enclave attestation and signing capabilities |
| [analytics](./library/analytics.md) | library | Go Module | Analytics library providing read-only data access and pseudonymization |
| [coordinator](./library/coordinator.md) | library | Go Module | Core coordination library with provider registry, attestation, and payment systems |
| [EigenInferenceEnclaveCLI](./cli/eigeninferenceenclavecli.md) | cli | Swift Package | CLI tool for Secure Enclave operations and diagnostics |
