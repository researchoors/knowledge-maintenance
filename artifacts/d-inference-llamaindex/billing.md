## Overview

Based on the provided context, the billing component is not a standalone service but rather an integrated subsystem within the Coordinator service. It handles provider compensation and consumer billing through integrated payment processing, utilizing Stripe for fiat payments and Solana USDC for crypto transactions. The billing subsystem manages deposits, pricing, referrals, and maintains an internal ledger, with operators retaining 95% of revenue.

## Architecture

The context does not provide specific file paths or submodules for a dedicated billing component. However, billing-related functionality is distributed across:

- **Coordinator Service** (Go, Confidential VM): Contains the billing/payment processing integration, connecting to Stripe as an external service
- **PostgreSQL Database**: Stores billing data including `provider_earnings` table for tracking compensation
- **Web Frontend** (`src/lib/api.ts`): Exposes payment processing functionality to consumers through the API abstraction layer
- **EigenInference App** (`StatusViewModel.swift`): Displays wallet/earnings data to providers; CLI subcommands `wallet` and `earnings` query billing information

## Dependencies

- **Coordinator Service**: Billing is embedded within or tightly coupled to the coordinator, which orchestrates payment flows between consumers and providers
- **Analytics Service**: Has read-only access to the `provider_earnings` table via PostgreSQL, using it for earnings leaderboard aggregation and reporting
- **Web Frontend**: Depends on billing API endpoints for payment processing and displaying billing information to consumers
- **EigenInference App**: Depends on billing data through the Darkbloom CLI's `wallet` and `earnings` commands to display provider compensation

## API Surface

Based on the context, the following billing-related interfaces are exposed:

- **Web API** (`src/lib/api.ts`): Payment processing endpoints accessible through the centralized HTTP client
- **CLI Commands**: `darkbloom wallet` and `darkbloom earnings` subcommands for provider billing queries
- **Analytics Endpoints**: 
  - `GET /v1/leaderboard/earnings`: Returns earnings rankings with configurable scope (account/node), time window (24h/7d/30d/all), and limit
- **PostgreSQL Schema**: `provider_earnings` table accessible to analytics service with read-only privileges

## Security Considerations

- **Confidential VM**: The Coordinator (which houses billing) runs in a Confidential VM, providing hardware-level isolation for sensitive payment processing
- **Read-Only Database Access**: The Analytics service connects to PostgreSQL using a read-only database user with `SELECT`-only privileges, preventing unauthorized modification of billing data
- **Bearer Token Authentication**: API access to billing-related endpoints requires authentication via keychain-stored API keys
- **Keychain Integration**: The EigenInference app uses macOS Keychain Services for secure credential storage related to billing access

## Data Flow

1. **Consumer Payment Entry**: Consumer initiates a payment through the Web UI → API layer (`src/lib/api.ts`) encrypts and forwards request to Coordinator
2. **Payment Processing**: Coordinator processes the payment via Stripe integration (for fiat) or Solana USDC handling
3. **Ledger Update**: Internal ledger records the transaction, updating provider earnings in the `provider_earnings` PostgreSQL table
4. **Provider Compensation**: After deducting the platform's 5% share, the remaining 95% is allocated to the provider
5. **Provider Visibility**: Provider views earnings through the EigenInference app, which queries via `darkbloom earnings` CLI command → Coordinator API → PostgreSQL
6. **Analytics Reporting**: Analytics service queries `provider_earnings` table with read-only access to generate leaderboard and network overview statistics via `GET /v1/leaderboard/earnings` and `GET /v1/overview` endpoints