## Overview

The mdm-enrollment component provides Mobile Device Management (MDM) enrollment and ACME-based certificate provisioning for provider devices in the d-inference network. It serves as a critical layer in the four-layer attestation architecture by enabling independent verification of device security configuration through operating system management interfaces. This component ensures that provider devices can be cryptographically validated as managed and compliant before they are trusted to handle inference workloads.

## Architecture

Based on the available context, specific file paths and submodules for the mdm-enrollment component are not documented. However, the architecture documentation and patent claims indicate the following structural responsibilities:

- **MicroMDM Integration**: An MDM server component configured to independently query security configuration of provider devices through macOS management interfaces
- **ACME Certificate Provisioning**: A certificate authority subsystem configured to validate device attestation certificate chains signed by the hardware manufacturer (Apple)
- **Enrollment Workflow**: Handles device enrollment into the MDM system, enabling ongoing security posture monitoring and policy enforcement

The architecture diagram places MDM-related functionality within the "External Services" layer, interfacing with Apple Services and the Coordinator.

## Dependencies

- **Coordinator Service**: The coordinator relies on MDM attestation results as part of its multi-factor provider trust scoring and selection algorithm. The MDM server reports device compliance status that influences routing decisions.
- **EigenInferenceEnclave**: The Secure Enclave component generates cryptographic attestation blobs and certificate chains that the MDM/certificate authority infrastructure validates. The attestation blob includes system integrity status, hardware identity, and binary hash information that MDM independently verifies.
- **Provider (Darkbloom Agent)**: Provider devices must be enrolled in MDM to participate in the network. The hardened inference agent on provider devices is subject to MDM security policy queries and must respond to attestation challenges.

## API Surface

Specific endpoints are not documented in the provided context. Based on the architectural role described:

- **Device Enrollment Interface**: Mechanisms for registering Apple Silicon provider devices into the MDM system
- **Security Configuration Query API**: Interfaces for the coordinator to query MDM-verified security posture of provider devices (SIP status, Secure Boot, Authenticated Root Volume, etc.)
- **Certificate Validation Endpoint**: ACME-provisioned certificate chain validation for device attestation certificates signed by Apple's hardware root of trust
- **Compliance Status Reporting**: Real-time or on-demand reporting of device compliance state to the coordinator for provider selection decisions

## Security Considerations

- **Independent Verification**: The MDM layer provides attestation independence — it verifies device security configuration through OS management interfaces separately from the device's own self-attestation, preventing a compromised device from falsifying its security posture
- **Certificate Chain Validation**: The certificate authority validates device attestation certificate chains signed by Apple's hardware manufacturer root, establishing hardware-backed identity assurance
- **Four-Layer Attestation Model**: MDM enrollment is one of four attestation layers (Secure Enclave signatures, MDM-based independent verification, Apple Managed Device Attestation with Apple-signed certificate chains, and periodic challenge-response), creating defense-in-depth against attestation forgery
- **Security Posture Attributes**: MDM independently verifies the same security properties that the Secure Enclave attestation blob claims (SIP enabled, Secure Boot, Authenticated Root Volume, RDMA disabled), providing cross-validation

## Data Flow

1. **Enrollment Phase**: An Apple Silicon Mac operator requests to become a provider → The device is enrolled into MicroMDM → MDM profile is installed on the device → ACME certificate is provisioned, establishing a device identity certificate chain rooted in Apple's CA

2. **Attestation Query Phase**: Coordinator receives an inference request → Coordinator queries MDM server for the target provider device's security configuration → MDM server independently queries the device through macOS management interfaces → Device reports SIP status, Secure Boot state, ARV status, and other security properties → MDM returns compliance status to coordinator

3. **Certificate Validation Phase**: Provider device generates Secure Enclave-signed attestation blob → Attestation includes certificate chain → Certificate authority validates the chain against Apple-signed root certificates → Validation result confirms hardware identity authenticity

4. **Ongoing Monitoring Phase**: Coordinator periodically issues challenge-response attestations → MDM continuously monitors device compliance → Any deviation in security posture (e.g., SIP disabled) triggers trust revocation → Provider is removed from the routing pool