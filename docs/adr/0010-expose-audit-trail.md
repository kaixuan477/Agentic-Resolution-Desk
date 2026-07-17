# 10. Expose the audit trail as a read-only governance view

Date: 2026

## Status

Accepted

## Context

Every tool call and governance decision is already recorded in an append-only,
PII-redacted audit trail (ADR 0005). Until now that trail was only observable in
application logs. Reviewers and auditors need to *see* it — to confirm what an
agent did, verify that high-value refunds went through human approval, and answer
"who did what, when" — without shell access to logs.

## Decision

- **Read-only HTTP view.** Add `GET /audit` returning the trail as structured
  `AuditRecord`s, with optional `user_id` / `tool` filters and a `limit`. It is
  read-only and takes no side effects.
- **Redaction stays at write time.** Records are already redacted when written,
  so the endpoint performs no additional masking — there is a single, testable
  redaction seam rather than two.
- **No new datastore coupling for the view.** The endpoint reads the audit sink
  directly and does not depend on the workflow service or a database, so it is
  available even when the graph's Postgres checkpointer is not.
- **Surface it in the existing dashboard.** A static `audit.html` view consumes
  `GET /audit`, reusing the no-build dashboard from ADR 0009.

## Consequences

- Governance is observable through the same API/UI as the rest of the system.
- Because redaction is enforced at write time, the exposed view cannot leak PII
  that the trail itself doesn't already contain.
- The in-memory sink is process-local; a multi-replica or long-retention
  deployment would back the trail with the Postgres audit table (already
  anticipated in ADR 0005) and this endpoint would read from it unchanged.
