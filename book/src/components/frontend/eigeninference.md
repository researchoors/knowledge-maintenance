# EigenInference

| Property | Value |
|----------|-------|
| Kind | frontend |
| Language | swift-package |
| Root Path | `app/EigenInference/Sources/EigenInference` |
| Manifest | `app/EigenInference/Package.swift` |
| External Apps | darkbloom-coordinator, huggingface-hub, mlx-backend, macos-launch-services |

> macOS menu bar application for managing darkbloom provider with native SwiftUI interface

---

# EigenInference Component Analysis

## Overview

EigenInference is a macOS menu bar application built with SwiftUI that provides a desktop frontend for the Darkbloom distributed inference network. The application serves as a graphical wrapper around the Rust-based `darkbloom` CLI binary, providing an intuitive interface for running and managing AI inference providers on macOS systems. Despite its name suggesting "EigenInference," the codebase consistently refers to "Darkbloom" throughout the implementation.

## Architecture

The application follows a **Model-View-ViewModel (MVVM)** architecture pattern typical of SwiftUI applications, combined with a **Coordinator Pattern** for managing external process lifecycle. The architecture emphasizes:

- **Single source of truth**: Configuration is shared between the GUI app and CLI via TOML files
- **Process management**: The app spawns and monitors the Rust `darkbloom` binary as a subprocess
- **Real-time updates**: Live polling of system state and backend health
- **Menu-bar-first design**: Minimal UI that lives in the system menu bar with expandable windows

Key architectural decisions:
- Menu bar app with dynamic activation policy (switches between `.accessory` and `.regular` modes)
- Shared configuration with CLI tools via TOML files in `~/.darkbloom/`
- Process lifecycle management with automatic restart and crash recovery
- Hardware detection and performance monitoring
- Keychain integration for secure credential storage

## Key Components

### 1. **EigenInferenceApp.swift** - Main Application Entry Point
**Lines 22-230**: SwiftUI `App` struct that defines the application structure with multiple scenes (MenuBar, Settings, Dashboard, Setup, Doctor, Logs). Implements sophisticated activation policy management to behave like a proper macOS application when windows are open while maintaining menu-bar-only mode otherwise.

### 2. **StatusViewModel.swift** - Central State Management
**Lines 18-627**: ObservableObject that centralizes all application state including provider status, hardware information, wallet/earnings data, and settings. Manages periodic polling, configuration persistence, and coordinates between UI and backend processes.

### 3. **ProviderManager.swift** - Process Lifecycle Management
**Lines 23-283**: Manages the Rust `darkbloom` binary as a subprocess, including spawning, monitoring, crash detection, auto-restart logic, and clean shutdown. Implements exponential backoff for restart attempts and telemetry reporting for crashes.

### 4. **CLIRunner.swift** - Command Execution Interface
**Lines 24-225**: Centralizes execution of `darkbloom` subcommands with proper environment setup, PATH management, and output capture. Supports both blocking execution and streaming output modes.

### 5. **ConfigManager.swift** - Configuration Management
**Lines 48-208**: TOML parser and serializer for the shared `provider.toml` configuration file used by both the GUI app and CLI. Ensures single source of truth for all provider settings.

### 6. **MenuBarView.swift** - Primary User Interface
**Lines 8-340**: SwiftUI view for the menu bar dropdown, showing provider status, hardware information, quick controls, and navigation to other windows. Includes adaptive design system with Liquid Glass effects on macOS 14+.

### 7. **DashboardView.swift** - Detailed Status Display
Comprehensive dashboard showing provider metrics, hardware specifications, trust status, and detailed statistics in a card-based layout.

### 8. **ModelManager.swift** - ML Model Discovery
**Lines 42-214**: Scans the HuggingFace cache directory for downloaded MLX models, manages model downloads via `huggingface-cli`, and provides model selection interface.

### 9. **SecurityManager.swift** - Trust and Security
Manages hardware attestation, security posture evaluation, and trust level determination for the inference provider.

### 10. **TelemetryReporter.swift** - Error Reporting
**Lines 52-267**: Lightweight telemetry system that buffers and reports crashes, errors, and diagnostic events to the coordinator backend with debounced network delivery.

### 11. **DesignSystem.swift** - UI Design Tokens
**Lines 11-455**: Comprehensive design system with adaptive color palettes, typography scales, and reusable UI components following the Darkbloom brand guidelines.

### 12. **UpdateManager.swift** - Application Updates
Checks for and manages application updates from the coordinator backend, with version comparison and update notification logic.

## Data Flows

### Provider Lifecycle Flow
```mermaid
graph TD
    A[User clicks Start] --> B[StatusViewModel.start()]
    B --> C[CLIRunner.run(start)]
    C --> D[ProviderManager.spawnProcess()]
    D --> E[darkbloom serve subprocess]
    E --> F[stdout/stderr capture]
    F --> G[StatusViewModel.parseProviderOutput()]
    G --> H[UI state updates]
    H --> I[MenuBarView reflects status]
    
    E --> J[HTTP health check :8100]
    J --> K[StatusViewModel.pollProviderStatus()]
    K --> H
    
    E --> L[Process termination]
    L --> M[Auto-restart logic]
    M --> D
```

### Configuration Flow
```mermaid
graph TD
    A[User changes setting] --> B[StatusViewModel property]
    B --> C[ConfigManager.update()]
    C --> D[TOML serialization]
    D --> E[~/.darkbloom/provider.toml]
    E --> F[CLI reads same config]
    
    G[App launch] --> H[ConfigManager.load()]
    H --> I[TOML parsing]
    I --> J[StatusViewModel initialization]
```

### Hardware Detection Flow
```mermaid
graph TD
    A[App initialization] --> B[StatusViewModel.detectHardware()]
    B --> C[sysctlbyname for memory]
    B --> D[system_profiler SPHardwareDataType]
    B --> E[system_profiler SPDisplaysDataType]
    C --> F[Memory GB calculation]
    D --> G[Chip name parsing]
    E --> H[GPU core detection]
    F --> I[UI state update]
    G --> I
    H --> I
```

## External Dependencies

### External Libraries

The application has **zero external dependencies** according to the Package.swift manifest. All functionality is implemented using Apple's built-in frameworks:

- **SwiftUI** (built-in): Primary UI framework for all views, navigation, and state management. Used throughout the application for declarative UI construction.
- **Foundation** (built-in): Core system services including Process management, FileManager, URLSession, UserDefaults, JSON/TOML parsing, and timer functionality.
- **Combine** (built-in): Reactive programming framework used in StatusViewModel for @Published properties and ObservableObject conformance.
- **Security** (built-in): Keychain Services API for secure storage of API keys and credentials.
- **UserNotifications** (built-in): Local notification delivery for provider status changes and system events.
- **CryptoKit** (built-in): Used in SecurityManager for cryptographic operations and hardware attestation.
- **Testing** (built-in): Apple's testing framework used in the test suite with modern @Test syntax.

The deliberate choice to avoid third-party dependencies makes this a self-contained, lightweight application that relies entirely on Apple's stable system frameworks.

## API Surface

### Public Interfaces Exposed

**CLI Integration Points:**
- Binary resolution: `CLIRunner.resolveBinaryPath()` searches for `darkbloom` binary in standard locations
- Command execution: `CLIRunner.run(_:)` for running darkbloom subcommands with full output capture
- Streaming execution: `CLIRunner.stream(_:onLine:)` for real-time log monitoring

**Configuration Management:**
- Shared TOML config: `ConfigManager.load()` and `ConfigManager.save(_:)` for provider.toml management
- Config updates: `ConfigManager.update(_:)` for atomic configuration changes
- Path resolution: `ConfigManager.configPath` for determining config file location

**Process Management:**
- Provider lifecycle: `ProviderManager.start()`, `ProviderManager.stop()` for subprocess control
- Status monitoring: `ProviderManager.isRunning` published property
- Output capture: `ProviderManager.lastOutputLine` for real-time log parsing

**State Management:**
- Observable state: `StatusViewModel` exposes @Published properties for all UI-bound state
- Hardware detection: Automatic system profiling and capability detection
- Metrics tracking: Request counts, token generation, throughput monitoring

## External Systems

The application integrates with several external systems and infrastructure components:

### Infrastructure Services

1. **Darkbloom Coordinator Backend**
   - **Connection**: WebSocket and HTTPS endpoints at configurable URLs (default: api.darkbloom.dev)
   - **Authentication**: Bearer token authentication via keychain-stored API keys
   - **Health monitoring**: Regular connectivity checks and heartbeat maintenance
   - **Telemetry**: Error reporting and crash analytics via POST to `/v1/telemetry/events`

2. **HuggingFace Model Hub**
   - **Model discovery**: Scans `~/.cache/huggingface/hub/` for downloaded MLX models
   - **Download integration**: Shells out to `huggingface-cli download` for model acquisition
   - **Cache management**: Respects HuggingFace caching conventions and directory structure

3. **MLX Backend Service**
   - **Local HTTP server**: Communicates with MLX inference backend on port 8100
   - **Health checks**: Regular polling of `/health` endpoint for backend status
   - **Model loading**: Coordinates model selection and loading with MLX runtime

### System Services

1. **macOS Launch Services**
   - **Auto-start**: LaunchAgent plist management for system startup integration
   - **Activation policy**: Dynamic switching between menu bar and full app modes
   - **Process monitoring**: Integration with macOS process lifecycle management

2. **macOS Security Framework**
   - **Keychain Services**: Secure credential storage and retrieval
   - **Hardware attestation**: System integrity verification and trust establishment
   - **Secure enclave**: Hardware-backed security validation when available

3. **File System Integration**
   - **Shared configuration**: TOML files in Application Support directory
   - **Model cache**: HuggingFace cache directory scanning and management
   - **Log aggregation**: Coordination with system logging infrastructure

## Component Interactions

The EigenInference component operates as a standalone desktop application with **no direct interactions** with other components in the d-inference codebase. However, it maintains several important integration patterns:

### External Component Communication

1. **Darkbloom CLI Binary**
   - **Type**: Process spawning and command execution
   - **Protocol**: Command-line interface with argument passing
   - **Description**: The GUI app wraps and manages the Rust-based darkbloom CLI binary, executing subcommands like `start`, `stop`, `wallet`, `earnings`, and `doctor`. Shared configuration ensures consistency between GUI and CLI operations.

2. **Darkbloom Coordinator Service**
   - **Type**: Network API calls
   - **Protocol**: HTTPS and WebSocket
   - **Description**: Connects to the distributed inference coordinator for provider registration, job routing, earnings tracking, and telemetry reporting. Uses configurable coordinator URLs with Bearer token authentication.

3. **MLX Inference Backend**
   - **Type**: Local HTTP API
   - **Protocol**: HTTP REST
   - **Description**: Monitors and interacts with the local MLX inference server on port 8100, performing health checks and status monitoring to reflect backend state in the GUI.

### Configuration Sharing

The application implements a **shared configuration model** where both the GUI app and CLI tools read/write the same TOML configuration files:

- `~/.darkbloom/provider.toml` - Provider settings, model configuration, and coordinator endpoints
- `~/Library/Application Support/darkbloom/` - Application-specific settings and cache

This ensures that changes made in either the GUI or CLI are immediately reflected in both interfaces, maintaining a consistent user experience.


---

## Dependency Connections

- → **darkbloom** (subprocess) — Manages darkbloom binary lifecycle through subprocess spawning and monitoring
