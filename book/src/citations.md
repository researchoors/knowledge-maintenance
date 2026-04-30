# Code Citations

Total citations: **158**

| # | File | Lines | Section | Claim |
|---|------|-------|---------|-------|
| 1 | `Sources/EigenInference/EigenInferenceApp.swift` | 22-24 | Key Components | Main SwiftUI App struct with NSApplicationDelegateAdaptor for activation policy  |
| 2 | `Sources/EigenInference/StatusViewModel.swift` | 18-25 | Key Components | Central ObservableObject managing provider state with @Published properties |
| 3 | `Sources/EigenInference/ProviderManager.swift` | 23-26 | Key Components | ProviderManager as ObservableObject managing darkbloom subprocess lifecycle |
| 4 | `Sources/EigenInference/CLIRunner.swift` | 24-32 | Key Components | CLIRunner class centralizes darkbloom binary execution with path resolution |
| 5 | `Sources/EigenInference/ConfigManager.swift` | 48-65 | Key Components | ConfigManager enum provides TOML parsing for shared provider.toml configuration |
| 6 | `Package.swift` | 4-7 | External Dependencies | Swift package with zero external dependencies, only built-in Apple frameworks |
| 7 | `Sources/EigenInference/EigenInferenceApp.swift` | 123-125 | Architecture | App starts as .accessory (menu bar only) and switches to .regular when windows o |
| 8 | `Sources/EigenInference/StatusViewModel.swift` | 216-262 | Data Flows | Real-time provider status polling via HTTP health checks on port 8100 |
| 9 | `Sources/EigenInference/ProviderManager.swift` | 207-233 | Data Flows | Auto-restart logic with exponential backoff and maximum retry limits |
| 10 | `Sources/EigenInference/StatusViewModel.swift` | 346-358 | Data Flows | Hardware detection using sysctlbyname and system_profiler commands |
| 11 | `Sources/EigenInference/ConfigManager.swift` | 50-65 | Component Interactions | Shared configuration path with CLI tools via ~/.darkbloom/provider.toml |
| 12 | `Sources/EigenInference/TelemetryReporter.swift` | 52-77 | External Systems | Telemetry reporter for crash analytics and error reporting to coordinator backen |
| 13 | `Sources/EigenInference/ModelManager.swift` | 56-59 | External Systems | HuggingFace cache directory scanning for MLX model discovery |
| 14 | `Sources/EigenInference/StatusViewModel.swift` | 527-538 | External Systems | Keychain Services integration for secure API key storage |
| 15 | `Sources/EigenInference/MenuBarView.swift` | 8-12 | Key Components | MenuBarView as primary user interface with ObservedObject pattern |
| 16 | `Sources/EigenInference/DesignSystem.swift` | 11-83 | Key Components | Comprehensive design system with adaptive color palettes for light/dark modes |
| 17 | `Tests/EigenInferenceTests/ConfigManagerTests.swift` | 3-5 | Architecture | Modern Swift Testing framework usage with @Test syntax instead of XCTest |
| 18 | `Sources/EigenInference/EigenInferenceApp.swift` | 27-58 | Architecture | Multiple SwiftUI scenes including MenuBarExtra, Settings, and various windows |
| 19 | `Sources/EigenInference/ProviderManager.swift` | 147-162 | Component Interactions | Environment setup matching CLIRunner for consistent tool discovery |
| 20 | `Sources/EigenInference/StatusViewModel.swift` | 302-320 | External Systems | Earnings and wallet integration via coordinator HTTP endpoints |
| 21 | `Sources/EigenInferenceEnclave/SecureEnclaveIdentity.swift` | 36-38 | Key Components | SecureEnclaveIdentity manages hardware-bound P-256 signing keys |
| 22 | `Sources/EigenInferenceEnclave/SecureEnclaveIdentity.swift` | 46-49 | Key Components | Creates new identity by generating P-256 key in Secure Enclave |
| 23 | `Sources/EigenInferenceEnclave/Attestation.swift` | 44-59 | Key Components | AttestationBlob contains hardware identity and security state fields |
| 24 | `Sources/EigenInferenceEnclave/Attestation.swift` | 100-131 | Data Flows | AttestationService creates attestations with deterministic JSON encoding |
| 25 | `Sources/EigenInferenceEnclave/Bridge.swift` | 36-41 | Key Components | FFI bridge provides C-callable functions with proper memory management |
| 26 | `Sources/EigenInferenceEnclave/Bridge.swift` | 79-90 | API Surface | FFI sign function takes raw data and returns base64-encoded signature |
| 27 | `Sources/EigenInferenceEnclaveCLI/main.swift` | 31-52 | Key Components | CLI attest command generates ephemeral attestations with optional parameters |
| 28 | `Sources/EigenInferenceEnclave/Attestation.swift` | 175-194 | External Dependencies | getChipName() uses system_profiler to extract Apple Silicon chip information |
| 29 | `Sources/EigenInferenceEnclave/Attestation.swift` | 260-273 | External Dependencies | checkSIPEnabled() calls csrutil status to determine SIP state |
| 30 | `Sources/EigenInferenceEnclave/Attestation.swift` | 118-126 | Data Flows | JSON encoder uses sortedKeys for deterministic output matching Go implementation |
| 31 | `Sources/EigenInferenceEnclave/SecureEnclaveIdentity.swift` | 100-103 | API Surface | Sign operation returns DER-encoded ECDSA signature compatible with Go crypto/ecd |
| 32 | `Sources/EigenInferenceEnclave/SecureEnclaveIdentity.swift` | 75-77 | API Surface | Public key is exported as raw 64-byte representation (X||Y without prefix) |
| 33 | `include/eigeninference_enclave.h` | 17 | API Surface | FFI provides Secure Enclave availability check function |
| 34 | `include/eigeninference_enclave.h` | 80-84 | API Surface | Full attestation function supports optional encryption key and binary hash bindi |
| 35 | `Sources/EigenInferenceEnclave/Attestation.swift` | 139-157 | Data Flows | Static verify method re-encodes attestation for signature validation |
| 36 | `Package.swift` | 7-10 | Architecture | Package provides both static library and executable CLI tool products |
| 37 | `Tests/EigenInferenceEnclaveTests/SecureEnclaveTests.swift` | 18-24 | API Surface | Identity creation produces 64-byte raw P-256 public keys |
| 38 | `Tests/EigenInferenceEnclaveTests/SecureEnclaveTests.swift` | 83-98 | Data Flows | Attestation service creates verifiable signed attestation blobs |
| 39 | `Tests/EigenInferenceEnclaveTests/AttestationTests.swift` | 52-68 | Data Flows | JSON output uses sorted keys for deterministic encoding |
| 40 | `Sources/EigenInferenceEnclave/Attestation.swift` | 235-253 | Security Model | RDMA check ensures remote memory access is disabled for security |
| 41 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 1-15 | Overview | CLI imports CryptoKit and EigenInferenceEnclave, provides command-line attestati |
| 42 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 16-29 | Key Components | printUsage function defines command structure with attest and info commands |
| 43 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 31-52 | Key Components | cmdAttest function handles attestation generation with optional parameters |
| 44 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 54-73 | Key Components | cmdInfo function displays Secure Enclave availability and ephemeral key info |
| 45 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 32-35 | Data Flows | Secure Enclave availability is checked before operations |
| 46 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 37-39 | Internal Dependencies | Creates ephemeral SecureEnclaveIdentity and AttestationService for each invocati |
| 47 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 41-44 | API Surface | Uses JSONEncoder with sortedKeys for deterministic output |
| 48 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 77-117 | Key Components | Main function provides argument parsing and command dispatch |
| 49 | `enclave/Sources/EigenInferenceEnclaveCLI/main.swift` | 87-104 | Key Components | Manual argument parsing handles --encryption-key and --binary-hash options |
| 50 | `enclave/Sources/EigenInferenceEnclaveCLI/WebSocketBridge.swift` | 1-3 | Key Components | WebSocketBridge is a stub indicating removed TLS bridge functionality |
| 51 | `enclave/Package.swift` | 9 | Overview | CLI is built as executable target named eigeninference-enclave |
| 52 | `enclave/Package.swift` | 13-16 | Internal Dependencies | CLI target depends on EigenInferenceEnclave library |
| 53 | `enclave/Package.swift` | 6 | External Dependencies | Requires macOS 13.0 or later for Secure Enclave support |
| 54 | `analytics/cmd/analytics/main.go` | 19-28 | Key Components | The service entry point initializes structured logging and loads configuration w |
| 55 | `analytics/cmd/analytics/main.go` | 84-93 | Architecture | Backend selection pattern allows memory or PostgreSQL storage based on configura |
| 56 | `analytics/internal/config/config.go` | 17-24 | Key Components | Configuration structure includes address, backend type, database URL, CORS origi |
| 57 | `analytics/internal/config/config.go` | 47-65 | Key Components | Backend-specific validation ensures required parameters for PostgreSQL mode |
| 58 | `analytics/internal/httpapi/server.go` | 24-41 | API Surface | Health check endpoint tests backend connectivity and returns status with timesta |
| 59 | `analytics/internal/httpapi/server.go` | 57-99 | API Surface | Earnings leaderboard endpoint supports scope, window, and limit query parameters |
| 60 | `analytics/internal/leaderboard/store.go` | 19-24 | Key Components | Leaderboard supports account and node scopes for different aggregation levels |
| 61 | `analytics/internal/leaderboard/store.go` | 27-33 | Key Components | Time window filtering supports 24h, 7d, 30d, and all-time periods |
| 62 | `analytics/internal/leaderboard/store.go` | 144-185 | Data Flows | Service layer handles query normalization, validation, and pseudonym generation  |
| 63 | `analytics/internal/leaderboard/store.go` | 477-496 | External Systems | PostgreSQL store implementation uses connection pooling and validates connectivi |
| 64 | `analytics/internal/leaderboard/store.go` | 517-546 | External Systems | PostgreSQL overview query uses CTEs for efficient provider and earnings statisti |
| 65 | `analytics/internal/pseudonym/alias.go` | 21-33 | Key Components | Pseudonym generator uses HMAC-SHA256 with kind prefixing to create deterministic |
| 66 | `analytics/internal/pseudonym/alias.go` | 35-107 | Key Components | Alias format uses predefined adjectives, animals, and numbers for human-readable |
| 67 | `analytics/go.mod` | 5 | External Dependencies | Primary external dependency is pgx/v5 for PostgreSQL connectivity |
| 68 | `analytics/README.md` | 3-12 | Overview | Service is designed to sit beside coordinator as standalone read-only analytics  |
| 69 | `analytics/README.md` | 71-81 | External Systems | PostgreSQL mode requires read-only user with SELECT privileges on analytics tabl |
| 70 | `cmd/coordinator/main.go` | 1-24 | Overview | The coordinator runs in a GCP Confidential VM with hardware-encrypted memory and |
| 71 | `internal/api/server.go` | 99-207 | Architecture | Server struct implements hexagonal architecture with clear separation between ex |
| 72 | `internal/registry/registry.go` | 330-362 | Key Components | Registry manages 1000+ concurrent providers with trust levels and intelligent ro |
| 73 | `internal/store/interface.go` | 22-354 | Key Components | Store interface abstracts persistence layer supporting PostgreSQL and in-memory  |
| 74 | `internal/payments/payments.go` | 1-22 | Key Components | Payment system uses double-entry accounting with micro-USD precision for blockch |
| 75 | `go.mod` | 5-14 | External Dependencies | Primary runtime dependencies include WebSocket, PostgreSQL, JWT, and cryptograph |
| 76 | `internal/api/server.go` | 766-937 | API Surface | API routes include OpenAI-compatible inference endpoints and administrative inte |
| 77 | `internal/registry/registry.go` | 1112-1245 | Key Components | Scoring algorithm considers provider load, hardware specs, trust level, and mode |
| 78 | `internal/api/consumer.go` | 38-64 | Data Flows | Request timeouts and retry logic handle provider failures and capacity constrain |
| 79 | `cmd/coordinator/main.go` | 78-131 | External Systems | Supports both PostgreSQL for production and in-memory store for development with |
| 80 | `internal/registry/registry.go` | 727-840 | Data Flows | Provider registration includes model catalog filtering and hardware attestation  |
| 81 | `internal/api/server.go` | 1040-1094 | API Surface | Authentication supports both Privy JWTs and API keys with different access level |
| 82 | `internal/ratelimit/ratelimit.go` | 1-50 | Key Components | Rate limiting uses per-account token buckets with separate tiers for inference v |
| 83 | `cmd/coordinator/main.go` | 184-207 | External Systems | Datadog integration provides APM tracing, metrics, and log forwarding |
| 84 | `cmd/coordinator/main.go` | 410-451 | External Systems | MDM integration enables independent provider security verification via MicroMDM |
| 85 | `cmd/coordinator/main.go` | 314-367 | Key Components | End-to-end encryption uses X25519 keys derived from BIP39 mnemonic for coordinat |
| 86 | `internal/registry/registry.go` | 1604-1634 | Key Components | Background eviction loop removes stale providers every 30 seconds based on heart |
| 87 | `cmd/coordinator/main.go` | 557-605 | Key Components | Model catalog seeding includes hardcoded models with size and architecture metad |
| 88 | `Dockerfile` | 24-31 | External Systems | Deployment includes MicroMDM and step-ca integration with environment configurat |
| 89 | `internal/api/server.go` | 989-997 | Architecture | Middleware stack includes CORS, panic recovery, and structured request logging |
| 90 | `src/main.rs` | 1-25 | Architecture | Darkbloom is the provider agent for Apple Silicon Macs with comprehensive archit |
| 91 | `src/main.rs` | 85-97 | Key Components | CatalogModel struct defines the model metadata structure with fields for ID, dis |
| 92 | `provider/Cargo.toml` | 1-10 | Analysis Data | The component is named 'darkbloom' version 0.4.7 with description 'EigenInferenc |
| 93 | `src/coordinator.rs` | 1-15 | Key Components | WebSocket client manages provider connection with automatic reconnection, regist |
| 94 | `src/security.rs` | 1-16 | Key Components | Security module implements runtime protections including PT_DENY_ATTACH, SIP ver |
| 95 | `src/backend/mod.rs` | 1-16 | Key Components | Backend management supports vllm-mlx and mlx-lm with health monitoring, automati |
| 96 | `src/hardware.rs` | 1-15 | Key Components | Hardware detection queries macOS system APIs for memory size, CPU cores, machine |
| 97 | `src/crypto.rs` | 1-16 | Key Components | NodeKeyPair implements ephemeral X25519 key pairs for E2E encryption, generated  |
| 98 | `src/models.rs` | 1-18 | Key Components | Model scanning examines HuggingFace cache for MLX models, filtering by available |
| 99 | `src/hypervisor.rs` | 1-34 | Key Components | Hypervisor integration uses Apple's framework to create lightweight VM with Stag |
| 100 | `src/proxy.rs` | 1-11 | Key Components | Request proxy handles legacy/local flows between coordinator WebSocket and local |

*...and 58 more*
