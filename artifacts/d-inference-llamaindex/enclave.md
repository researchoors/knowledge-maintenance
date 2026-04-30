## Overview

The enclave component (EigenInferenceEnclave) is a Swift library that provides Secure Enclave integration for the d-inference system, enabling hardware-bound cryptographic key management, signed attestation blob generation, and cross-language interoperability via an FFI bridge. It serves as the trust root for provider nodes by establishing cryptographically verifiable hardware identity and security posture that the coordinator uses to validate providers before routing inference requests.

## Architecture

- **`enclave/Sources/EigenInferenceEnclave/Attestation.swift`** — Builds signed attestation blobs containing hardware identity (chip name, hardware model, serial number), security state (SIP, Secure Boot, Authenticated Root, RDMA status), public keys (P-256 signing key from Secure Enclave, optional X25519 encryption key), and an ISO 8601 timestamp. Blobs are JSON-encoded with sorted keys for deterministic serialization matching Go's `encoding/json` output, then signed with the Secure Enclave P-256 key.

- **`SecureEnclaveIdentity.swift`** — Manages Secure Enclave key operations including ephemeral P-256 key generation, signing, and verification. Exposes a `publicKeyBase64` property for key export.

- **`Bridge.swift`** — Provides an FFI bridge for cross-language integration, enabling other d-inference components (e.g., the Rust provider) to invoke Secure Enclave operations.

## Dependencies

**Internal:** This component has no direct internal dependencies within the d-inference codebase.

**External/System:**
- **CryptoKit** (System) — Used throughout `SecureEnclaveIdentity.swift` and `Bridge.swift` for key generation, signing, and verification.
- **Foundation** (System) — Provides core data types (`Data`, `Date`, `String`), JSON encoding/decoding (`JSONEncoder`, `JSONDecoder`), and process execution (`Process`, `Pipe`) for system information gathering.
- **system_profiler** — Extracts hardware information (chip name, serial number) for attestation blobs, called via `Process` in `getChipName()` and `getSerialNumber()`.
- **csrutil** — Checks System Integrity Protection status, called in `checkSIPEnabled()`.
- **diskutil** — Verifies Authenticated Root Volume status and retrieves system volume hash, called in `checkAuthenticatedRootEnabled()` and `getSystemVolumeHash()`.
- **rdma_ctl** — Verifies RDMA is disabled (security requirement), called in `checkRDMADisabled()`.

## API Surface

- **`SecureEnclaveIdentity`** — Class for creating ephemeral P-256 signing keys within the Secure Enclave. Provides `publicKeyBase64` property for key export and methods for signing data.
- **`AttestationService`** — Instantiated with a `SecureEnclaveIdentity`; exposes `createAttestation()` method that generates signed attestation blobs, supporting optional encryption key binding and binary hash inclusion.
- **`AttestationBlob`** — Public `Codable` struct representing the attestation payload with fields: `authenticatedRootEnabled`, `binaryHash` (optional), `chipName`, `encryptionPublicKey` (optional), `hardwareModel`, `osVersion`, `publicKey`, `rdmaDisabled`, `secureBootEnabled`, `secureEnclaveAvailable`, `serialNumber`, `sipEnabled`, `systemVolumeHash`, and `timestamp`.
- **`SecureEnclave.isAvailable`** — Global availability check used before any Secure Enclave operations to prevent runtime failures on unsupported hardware (e.g., Intel Macs).

## Security Considerations

- **Hardware-bound keys:** P-256 keys are generated within the Secure Enclave, meaning private key material never leaves the hardware — only the public key and signatures are exportable.
- **Signed attestation:** Attestation blobs are signed with the Secure Enclave P-256 key, allowing the coordinator to cryptographically verify the attestation originated from genuine Secure Enclave hardware.
- **Key binding:** The optional `encryptionPublicKey` field binds the provider's X25519 encryption key to its Secure Enclave identity, proving the same physical device controls both the signing key (for attestation) and the encryption key (for encrypted inference).
- **Deterministic serialization:** JSON encoding uses `.sortedKeys` to ensure identical output across Swift and Go implementations, which is critical for signature verification across languages.
- **Software security checks as placeholders:** SIP and Secure Boot checks are currently software-based (calling `csrutil` and making assumptions about Apple Silicon). Production deployments would use Managed Device Attestation (MDA) via Apple Business Manager for hardware-attested evidence.
- **Ephemeral key model:** All keys are generated fresh per invocation with no persistent state, reducing the attack surface associated with key storage.

## Data Flow

1. **Entry:** A consumer (e.g., `EigenInferenceEnclaveCLI` or the FFI bridge) requests an attestation by creating a `SecureEnclaveIdentity`, which generates an ephemeral P-256 key pair inside the Secure Enclave.
2. **Information gathering:** `AttestationService.createAttestation()` invokes system utilities via `Process` — `system_profiler` for chip name and serial number, `csrutil` for SIP status, `diskutil` for Authenticated Root and system volume hash, and `rdma_ctl` for RDMA status.
3. **Blob construction:** The collected hardware info, security state, public key, optional encryption key binding, optional binary hash, and current timestamp are assembled into an `AttestationBlob` struct.
4. **Serialization:** The blob is JSON-encoded with sorted keys for deterministic output.
5. **Signing:** The JSON payload is signed using the Secure Enclave P-256 key, producing a DER-encoded ECDSA signature.
6. **Exit:** The signed attestation (blob + signature) is returned to the caller, typically for inclusion in provider registration messages to the coordinator, where the signature is verified against the Secure Enclave public key.