# ADR-015 — Web client in a separate repository with a service boundary

**Status:** Proposed
**Date:** 2026-10-08
**Deciders:** BE1, BE2, FE, DO
**Related:** SRS 3.1.3, 4.1.1; TECHNICAL_DESIGN 1.3, 4, 4.4, 11.1; CURRENT_STATE D-90, D-58, Q-67, Q-62

## Context
TECHNICAL_DESIGN 4 places the web app in `web/` of `cryptopilot_project`, with
`features/<module>/{api,components,hooks,pages}` and `shared/`. That folder holds only a `.gitkeep`;
the web client was started instead in its own repository, `cryptopilot-frontend`
(`https://github.com/huyhv-se180722/cryptopilot-frontend`, branch `develop`), with a layered structure
and lint rules that keep transport code out of the screens. Most backend modules the screens need are
still PLANNED (fe-guide `06-task-map.md`), so the client must be built before its endpoints exist,
without inventing endpoints and without letting development data reach a production build. Two
repositories also mean the documents in this repository cannot see the web code, which affects
`docs/tools/check_traceability.py` (it searches `web/src`).

## Decision
The web client lives in the separate repository `cryptopilot-frontend`; `web/` in `cryptopilot_project`
stays empty. Its code follows one direction — page → feature hook → service interface → HTTP or
realtime adapter → backend — enforced by ESLint: screens never call `fetch` or `WebSocket` and never
import services or development data. Every adapter decodes the response body at runtime before it
becomes a typed value; a service whose backend endpoint is not merged rejects with `NOT_CONFIGURED`
instead of returning made-up data. Development data, including a labelled development sign-in, lives
only in `src/dev`, is switched on by `VITE_ENABLE_DEV_FIXTURES` in development mode only, shows a
visible banner, is never a fallback for a failed request, and fails the production build if bundled.
The backend contract the client follows is `docs/design/fe-guide/`; the client's status, decisions and
questions are kept in `CURRENT_STATE.md` with the shared ids, not in a parallel system.

## Consequences
Positive: screens can be built and reviewed against the fe-guide contract before an endpoint merges,
and switching to the real endpoint replaces one adapter, not the screens. Production cannot show
development data. The web repository has its own CI and pull requests, so FE work does not block the
backend pipeline.

Negative: two repositories to clone and keep in step; a contract change needs a fe-guide re-sync and
then an adapter change. The traceability tool and the folder tree of TECHNICAL_DESIGN 4 do not cover the
web code until Q-62 is answered. Plan-tier gating in the client is display only (D-58); the backend
remains the authority on every request.

This holds while the fe-guide is re-synced after each backend PR that touches a controller, a DTO,
`ErrorCode`, `SecurityConfig` or `WebSocketConfig`, as its README requires.

## Alternatives considered
Move the client into `web/` of `cryptopilot_project`: rejected for now because the client already has
its own history, CI and review flow, and moving it would mix FE pull requests into the backend
pipeline; it stays possible later because the client has no dependency on the monorepo layout.
Use the folder tree of TECHNICAL_DESIGN 4 (`features/*/api`, `shared/`): not adopted because the
service seams (`services/api`, `services/auth`, `services/websocket`) and the composition root
(`app/providers`) are what the lint rules protect; the feature folders keep `components`, `hooks` and
`schemas` as TECHNICAL_DESIGN 4 intends.
Mock server or client-side fake API in production builds: rejected; it hides missing integration and
can show invented market data, which SRS 3.3 and the scope boundary forbid.
