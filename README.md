Google Merchant Feed Sync Service
Overview

This service synchronizes product data from a PostgreSQL database into a Google Merchant–compliant Google Sheets feed.
It is designed as a standalone integration service, decoupled from core store logic, enabling safe, repeatable feed generation.

Key Features

PostgreSQL → Google Sheets synchronization

Google Merchant–compliant schema

Idempotent inserts and updates

Automatic deletion of inactive products

Inventory-aware availability handling

Service Account–based authentication

Re-runnable without duplication


Architecture

```rust
PostgreSQL → Feed Sync Service → Google Sheets → Google Merchant Center
```

Responsibilities are intentionally isolated to keep the commerce platform and external integrations loosely coupled.