## Overview

The attestation component provides hardware-backed cryptographic attestation capabilities using Apple's Secure Enclave, establishing tamper-resistant device identities and generating cryptographically signed attestation blobs that prove a provider node's hardware and software security posture. It serves as the foundation for the d-inference system's zero-trust security model, enabling the coordinator to verify that provider nodes are running on genuine Apple Silicon hardware with proper security configurations. The component spans both Swift (provider-side attestation generation) and Go (coordinator-side verification), with cross-language cryptographic interoperability as a core design principle.

## Architecture

### Swift Provider-Side (EigenInferenceEnclave)

- **`Sources/EigenInferenceEnclave/SecureEnclaveIdentity.swift`** — Core identity management layer. Manages hardware-bound P-256 ECDSA signing keys stored in Apple's Secure Enclave hardware. Creates ephemeral or persistent device identities, provides multiple public key formats (base64, hex, raw bytes), and offers static verification methods for signature validation. Private keys never leave the Secure Enclave.

- **`Sources/EigenInferenceEnclave/Attestation.swift`** — Attestation service layer. Builds and signs attestation blobs containing system security state. Collects hardware info (chip name, serial number) and security status (SIP, Secure Boot, Authenticated Root Volume, RDMA). Creates deterministic JSON attestation blobs with sorted keys (matching Go's encoding/json map key ordering for cross-language verification). Contains the `AttestationBlob` struct with fields including `authenticatedRootEnabled`, `binaryHash`, and other hardware/security attributes.

- **`Sources/EigenInferenceEnclave/Bridge.swift`** — Foreign Function Interface (FFI) layer providing C-callable functions for Rust integration.

### Swift CLI (EigenInferenceEnclaveCLI)

- **`main.swift` (lines 77-117)** — Main entry point handling argument parsing and command dispatch for `attest` and `info` commands.
- **`main.swift` (lines 31-52)** — `cmdAttest` handler: generates signed attestation blobs with optional encryption key binding (`--encryption-key`) and binary hash inclusion (`--binary-hash`).
- **`main.swift` (lines 54-73)** — `cmdInfo` handler: displays Secure Enclave availability and generates ephemeral public key.

### Go Coordinator-Side (verify-attestation)

- **`coordinator/cmd/verify-attestation/main.go` (lines 10-34)** — Simple CLI utility that reads attestation data from `/tmp/eigeninference_attestation.json` and coordinates verification through the attestation package.
- **Lines 11-15** — File input handler reading attestation JSON with error handling.
- **Lines 17-21** — Delegates to `attestation.VerifyJSON()` for JSON unmarshaling and cryptographic verification.
- **Lines 23-33** — Results display handler formatting hardware identity, security status, and verification outcome.
- **Lines 14, 20, 32** — Exit code management (0 for success, 1 for failure) for automation integration.

## Dependencies

### Internal Dependencies
- **EigenInferenceEnclave → EigenInferenceEnclaveCLI**: The CLI is a thin wrapper around the library, using `SecureEnclaveIdentity` for key management, `AttestationService` for attestation generation, and `SecureEnclave.isAvailable` for availability checks.
- **verify-attestation → coordinator attestation package**: The Go utility delegates verification to `attestation.VerifyJSON()`.

### External/System Dependencies
- **CryptoKit** (Apple): Secure Enclave integration, P-256 ECDSA key generation, signing, and verification.
- **Foundation** (Apple): Core data types, JSON encoding/decoding (`JSONEncoder`/`JSONDecoder` with `.sortedKeys`), process execution.
- **system_profiler** (`/usr/sbin/system_profiler`): Extracts hardware information (chip name, serial number) for attestation blobs.
- **csrutil** (`/usr/bin/csrutil`): Checks System Integrity Protection status.
- **diskutil** (`/usr/sbin/diskutil`): Verifies Authenticated Root Volume status and system volume integrity.
- **rdma_ctl** (`/usr/bin/rdma_ctl`): Verifies RDMA is disabled (security requirement).

## API Surface

### Swift Library APIs
- **`SecureEnclaveIdentity`**: Creates ephemeral/persistent P-256 ECDSA identities; exposes `publicKeyBase64`, `publicKeyHex`, raw bytes; provides hardware-isolated signing and static signature verification methods.
- **`AttestationService`**: `createAttestation()` method generates signed attestation blobs with optional encryption key binding and binary hash inclusion.
- **`AttestationBlob`** (Codable struct): Contains `authenticatedRootEnabled`, `binaryHash`, and other hardware/security fields, serialized with sorted keys for deterministic output.

### CLI Commands
- **`attest`**: Generates signed attestation blobs. Options: `--encryption-key` (binds X25519 encryption key to SE identity), `--binary-hash` (includes binary hash in attestation).
- **`info`**: Outputs JSON with `secure_enclave_available`, `key_persistence` ("ephemeral"), and `public_key` (base64-encoded P-256).

### Go Verification API
- **`attestation.VerifyJSON()`**: Accepts raw JSON bytes, unmarshals into attestation structure, and performs cryptographic verification of the P-256 ECDSA signature.

## Security Considerations

1. **Hardware-Isolated Key Storage**: Private keys never leave the Secure Enclave hardware; all signing operations execute within the secure enclave boundary.

2. **Cross-Language Signature Verification**: P-256 ECDSA signatures created by Swift Secure Enclave modules are verified by the Go coordinator, ensuring attestation blobs haven't been tampered with and originate from genuine Secure Enclave hardware.

3. **Deterministic JSON Serialization**: Attestation blobs use sorted keys (Swift's `JSONEncoder` with `.sortedKeys`) matching Go's `encoding/json` map key ordering, ensuring identical byte-level representation for signature verification across languages.

4. **Key Binding**: The optional `encryptionPublicKey` field cryptographically binds the provider's X25519 encryption key to its Secure Enclave identity, proving the same physical device controls both the signing key (for attestation) and the encryption key (for encrypted inference).

5. **Security State Attestation**: Includes verification of SIP status, Secure Boot, Authenticated Root Volume (sealed system volume), and RDMA disabled status.

6. **Software vs. Hardware Attestation Gap**: Current SIP and Secure Boot checks are software-based (calling `csrutil status`). Production deployments should use Managed Device Attestation (MDA) via Apple Business Manager for hardware-attested evidence. The software checks are documented as development placeholders.

7. **Ephemeral Key Design**: The CLI creates fresh cryptographic keys per invocation rather than persisting state, reducing key exposure risk.

8. **Exit Code Discipline**: Proper exit codes (0/1) enable secure integration with automation and CI/CD systems.

## Data Flow

### Attestation Generation (Provider Side)

1. CLI receives `attest` command with optional `--encryption-key` and `--binary-hash` flags.
2. Checks `SecureEnclave.isAvailable`; exits with error if unavailable (e.g., Intel Macs).
3. Creates ephemeral `SecureEnclaveIdentity` — P-256 ECDSA key generated within Secure Enclave hardware.
4. Instantiates `AttestationService` with the identity.
5. `AttestationService.createAttestation()`:
   - Calls `system_profiler` via `Process` to collect chip name and serial number.
   - Calls `csrutil` to check SIP status.
   - Calls `diskutil` to check Authenticated Root Volume and system volume hash.
   - Calls `rdma_ctl` to verify RDMA is disabled.
   - Builds `AttestationBlob` struct with all collected data plus timestamp (ISO 8601).
   - Signs the deterministic JSON blob with the Secure Enclave P-256 key.
6. Outputs JSON with sorted keys to stdout.

### Attestation Verification (Coordinator Side)

1. `verify-attestation` reads `/tmp/eigeninference_attestation.json`.
2. If file doesn't exist → prints error to stderr, exits with code 1.
3. Calls `attestation.VerifyJSON()` which:
   - Unmarshals JSON into attestation structure.
   - Extracts the P-256 public key from the attestation.
   - Verifies the ECDSA signature against the public key and canonical JSON.
   - Validates attestation content (hardware identity, security fields).
4. If verification fails → exits with code 1.
5. If verification succeeds → displays results (hardware identity, security status, verification outcome) and exits with code 0.