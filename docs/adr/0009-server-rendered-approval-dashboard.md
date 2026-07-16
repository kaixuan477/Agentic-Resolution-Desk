# 9. Server-rendered approval dashboard (no SPA build step)

Date: 2026

## Status

Accepted

## Context

Reviewers need a UI to see refunds awaiting approval and to approve or deny them.
Options ranged from a full single-page app (React/Vite) to a minimal
server-served page. The project's value is the agentic backend and its
governance; the dashboard is a thin operator console, not the product.

A heavy frontend toolchain would add a build step, a node dependency tree, and CI
complexity disproportionate to a small internal console.

## Decision

- **Vanilla static dashboard.** A single `index.html` + `styles.css` + `app.js`
  served by FastAPI via `StaticFiles` at `/dashboard/`. No bundler, no framework,
  no build step.
- **Reuse the existing JSON API.** The dashboard consumes `GET /pending/details`
  (snapshots incl. proposed tool / user / amount) and `POST /approve`. No
  dashboard-specific server logic beyond two read endpoints
  (`/pending/details`, `/workflows/{thread_id}`).
- **Snapshot carries the proposed action.** `WorkflowSnapshot` now exposes
  `proposed_tool`, `proposed_user_id`, and `proposed_amount`, extracted
  defensively so it works whether the checkpointer returns a Pydantic model or a
  plain dict.

## Consequences

- Zero frontend build; the console works by opening `/dashboard/`.
- The dashboard cannot drift from the API — it is just another client of it, and
  the same endpoints are covered by offline tests.
- Styling/interactivity are basic by design; a richer SPA can replace the static
  page later without any backend changes, since the contract is the JSON API.
