## Overview

The console-ui is a Next.js frontend application that serves as the primary user interface for Darkbloom's decentralized AI inference platform. It provides both a consumer-facing chat interface for AI interactions and a provider dashboard for hardware attestation management, billing, and node monitoring. Built with TypeScript, React, and Tailwind CSS, it acts as the gateway through which end users interact with the entire Darkbloom inference network.

## Architecture

- **`src/app/page.tsx`**: Main chat interface for AI conversations. Handles real-time streaming, trust verification badges, model selection, and the full data flow from user input → encryption → coordinator API → streaming response → UI update. Contains the system prompt defining the AI assistant's behavior and Darkbloom platform facts.

- **`src/app/providers/`**: Provider dashboard interface for hardware providers to monitor their nodes. Features real-time device status, earnings tracking, attestation warnings, Apple MDA certificate verification, hardware integrity monitoring, and metrics like token throughput and device health alerts.

- **`src/app/api-console/page.tsx`**: API console/reference page documenting the platform's REST API endpoints (chat completions, responses API, models listing) with example request/response payloads and notes on encryption and attestation metadata headers.

- **`src/hooks/useAuth.ts`**: Privy-based email authentication hook with API key management, automatic key provisioning, session management, and logout cleanup that clears sensitive data.

- **`src/components/providers/PrivyClientProvider.tsx`**: Privy authentication provider component wrapping the app with email-based auth and API key provisioning.

- **`src/lib/api.ts`**: Centralized HTTP client with encryption and streaming support. Handles model management, chat streaming, payment processing, and provider metrics. Implements optional NaCl Box encryption to coordinator with forward secrecy.

- **`src/lib/store.ts`**: Zustand-based client-side state management with localStorage persistence. Defines the `Message` type and central application store.

- **`src/hooks/useToast.ts`**: Toast notification system for user feedback.

- **`src/components/ChatMessage.tsx`**, **`src/components/ChatInput.tsx`**, **`src/components/TopBar.tsx`**, **`src/components/PreSendTrustBanner.tsx`**, **`src/components/InviteCodeBanner.tsx`**: UI components for the chat interface, including trust verification display and invite code redemption.

## Dependencies

- **Darkbloom Coordinator Backend**: The console-ui depends on the coordinator for all inference operations, model listings, provider data, and attestation information. Communication happens via HTTPS and WebSocket endpoints (default: api.darkbloom.dev) with Bearer token authentication.

- **Analytics Service**: The console-ui sends privacy-conscious telemetry events to the analytics service via `POST /api/telemetry`, enabling usage tracking without exposing sensitive data.

- **Privy Authentication Service**: External dependency for email-based authentication, providing identity verification and token management.

- **Stripe**: External payment processing dependency for credit purchases (`/api/payments/stripe/checkout`), provider onboarding (`/api/payments/stripe/onboard`), and withdrawal processing.

## API Surface

### HTTP API Endpoints (Next.js API Routes)

- **`GET /api/health`**: Health check returning coordinator status and provider count
- **`POST /api/chat`**: Streaming chat completions proxy to coordinator with encryption support
- **`GET /api/models`**: Available AI models listing from coordinator
- **`GET /api/encryption-key`**: Coordinator's public key for end-to-end encryption
- **`POST /api/auth/keys`**: API key provisioning using Privy authentication tokens
- **`GET /api/payments/balance`**: User account balance and withdrawable amounts
- **`GET /api/payments/usage`**: Detailed usage history with costs and token counts
- **`POST /api/payments/stripe/checkout`**: Stripe payment session creation for credit purchases
- **`GET /api/payments/stripe/status`**: Provider payout configuration status
- **`POST /api/payments/stripe/onboard`**: Stripe Connect Express onboarding for providers
- **`POST /api/payments/withdraw/stripe`**: Provider withdrawal requests to Stripe
- **`GET /api/payments/stripe/withdrawals`**: Provider withdrawal history
- **`POST /api/invite/redeem`**: Invite code redemption for account credits
- **`GET /api/me/providers`**: Provider device status and attestation information
- **`GET /api/me/summary`**: User account summary with provider and consumer activity
- **`POST /api/telemetry`**: Privacy-conscious analytics event tracking
- **`GET /api/pricing`**: Model pricing information in USD per token

### Client-Side Library Functions

- **`streamChat(messages, model, callbacks, ...)`**: Initiates encrypted streaming chat with the coordinator
- **`fetchModels()`**: Retrieves available model catalog from the coordinator

## Security Considerations

- **End-to-End Encryption**: Uses NaCl Box (X25519) encryption for coordinator communication. The client fetches the coordinator's public key via `/api/encryption-key` and encrypts prompts before transmission, ensuring node operators and the coordinator cannot read plaintext prompts.

- **Authentication**: Privy-based email authentication with automatic API key provisioning. Session management includes cleanup of sensitive data on logout and handling of key expiration events.

- **Attestation Verification**: The chat interface displays hardware attestation status and Secure Enclave verification via trust badges. Response headers include provider attestation metadata (`x-provider-attested`, `x-provider-trust-level`, `x-provider-chip`).

- **Pre-Send Trust Banner**: The `PreSendTrustBanner` component informs users about encryption and attestation status before they send messages, providing transparency about the security posture of their request.

- **Sensitive Data Cleanup**: The authentication system explicitly clears sensitive data on logout, preventing credential leakage from persisted state.

- **Forward Secrecy**: The NaCl Box encryption implementation includes forward secrecy for coordinator communication.

## Data Flow

**Chat Request Flow (primary use case):**

1. **User Input**: User types a message in `ChatInput` component and selects a model from the TopBar.
2. **State Update**: Message is added to the Zustand store with a generated ID (`generateId()`), creating a `Message` object with role "user".
3. **Pre-Send Trust Check**: `PreSendTrustBanner` displays encryption and attestation status before the message is sent.
4. **Encryption**: The `streamChat` function in `src/lib/api.ts` fetches the coordinator's public key from `/api/encryption-key` and encrypts the prompt using NaCl Box (X25519).
5. **API Proxy**: The encrypted payload is sent to `POST /api/chat` (Next.js API route), which proxies the request to the Darkbloom coordinator with Bearer token authentication.
6. **Coordinator Routing**: The coordinator routes the encrypted request to a hardware-attested Apple Silicon provider node. The coordinator cannot read the plaintext prompt.
7. **Streaming Response**: The provider node processes the inference and returns a streaming response through the coordinator back to the Next.js API route.
8. **UI Update**: The streaming chunks are received via callbacks in `streamChat`, updating the assistant's `Message` object in the Zustand store in real-time. The `ChatMessage` component renders the streaming response.
9. **Trust Metadata**: Response headers containing attestation metadata (`x-provider-attested`, `x-provider-trust-level`, `x-provider-chip`) are processed and displayed as trust verification badges in the UI.
10. **Analytics**: The interaction is tracked via `trackEvent` (Google Analytics) and `POST /api/telemetry` for privacy-conscious platform analytics.