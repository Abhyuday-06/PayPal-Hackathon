# Scope and trust boundaries

AgentGate is a single-owner sandbox prototype for a small, server-owned USD catalogue. It supports multiple agent identities and scoped owner budgets. It does not provide tenant isolation, arbitrary marketplaces, production payment authorization, refunds/disputes or AP2 compliance.

The LLM and seller descriptions are untrusted. Model output is schema-checked, then passed through the same gateway as direct requests. The model has no approval/capture credential. Separate agent keys bind request identity and permit only catalogue reads and proposals. The owner key signs an eight-hour HttpOnly session; browser mutations require the configured exact origin. Anyone with the owner key has full owner authority.

Mission planning adds a virtual allocation against the observed available funds. It does not lock or reserve live funds. Saved proposals can become unaffordable or expire before the owner reviews them. Mission approval rechecks the entire exact-cart set and reserves every new cart in one transaction or none. Worker recovery reuses persisted model decisions and deterministic proposal IDs. Seller edits affect only the descriptions given to the model for that mission; authoritative product fields are untouched.

All amounts use integer cents. Price, merchant and currency come from the server catalogue. Cart SHA256 binds SKU, quantity, price, currency and merchant; approvals expire and cannot be silently renewed. A transaction reserves budget before checkout. PostgreSQL per-budget advisory locks and SQLite immediate transactions protect concurrent owners/workers.

Durable leases commit external action intent before network I/O. Ambiguous outcomes retain reservations. A stable PayPal Request ID is reused for the same action; persisted receipts survive restart and repeated capture returns the recorded result. Read-only reconciliation never initiates capture. Signature-verified webhook metadata can queue authoritative recovery, but event amounts cannot mark a cart paid. Catalogue changes invalidate binding.

Remaining risks: compromise of backend credentials, catalogue administrator or owner key; provider outages; finite provider idempotency retention; lack of distributed rate limits; no independent security assessment; limited synthetic coverage. Uncertain create outcomes may require operator investigation because an order ID is not available for recovery after a lost creation reply. Do not release an uncertain reservation just because its approval expired. Backups and operator recovery remain required.
