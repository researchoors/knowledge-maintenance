# External Services

## Stripe

**Type:** payment_platform

Payment processing for consumer deposits and provider payouts

**Used by:** coordinator, web

## Datadog

**Type:** monitoring

APM tracing, metrics, and structured logging

**Used by:** coordinator, web

## PostgreSQL

**Type:** database

Primary data store for balances, usage, and provider state

**Used by:** coordinator, analytics

## Privy

**Type:** authentication

OAuth and email-based user authentication

**Used by:** web

## Apple Secure Enclave

**Type:** hardware_security

Hardware attestation and cryptographic signing

**Used by:** darkbloom, EigenInferenceEnclave

## Cloudflare R2

**Type:** cdn_storage

Model distribution and runtime package CDN

**Used by:** darkbloom

