## Overview

The provided context does not contain any information about a component called "image-bridge" or any Python FastAPI service bridging to Draw Things gRPC. The context covers the core d-inference architecture (Coordinator, Provider/Darkbloom Agent, Secure Enclave, MLX inference engine, EigenInference macOS app, and the wire protocol), but makes no reference to an image generation bridge.

## Architecture

No file paths or submodules related to "image-bridge" are present in the retrieved context.

## Dependencies

Cannot be determined from the provided context. The context describes dependencies for other components (e.g., EigenInferenceEnclave depends on CryptoKit, Foundation, system tools like `system_profiler`, `csrutil`, `diskutil`; EigenInference depends on the Darkbloom Coordinator, HuggingFace, MLX backend), but nothing related to an image-bridge component.

## API Surface

No API endpoints, functions, or types related to this component appear in the context.

## Security Considerations

The context describes security patterns used elsewhere in d-inference (Secure Enclave attestation, X25519/NaCl-box end-to-end encryption, PT_DENY_ATTACH, Hardened Runtime, SIP verification, MDM-based attestation), but none specific to an image-bridge component.

## Data Flow

Cannot be traced from the provided context. The only data flow described involves the core inference path: Consumer → Coordinator (HTTPS, OpenAI-compatible API) → Provider (WebSocket, outbound) → MLX inference engine → Apple Silicon GPU. No image generation or Draw Things gRPC flow is documented.