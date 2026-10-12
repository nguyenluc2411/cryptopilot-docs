# Changelog — FE integration guide

Newest first. Each entry names the `develop` SHA the guide was synced to.

## 2026-10-08 — re-sync, `develop` @ `0d92def`

- Alerts (T-054, PR #44) and the `expectedAlertCount` check of `DELETE /watchlist/{id}` are on
  `develop`: statuses and sources moved from the branch to `develop`. 41 REST endpoints implemented.
- Alert evaluation: PRICE alerts fire since T-055 (PR #51); INDICATOR alerts are not evaluated (T-110).
- CORS for REST and `/ws` from one list, `CORS_ALLOWED_ORIGINS` (D-83, PR #50): 01-setup and
  05-realtime rewritten; M-02 and M-03 resolved; the proxy is optional.
- `PATCH /watchlist/{id}`: `sortOrder` 0–10000, MSG15 outside.
- 12 moved line references updated (`SecurityConfig`, `WebSocketConfig`, `application.yml`,
  `UpdateWatchlistItemRequest`, `WatchlistController`, `WatchlistServiceImpl`).
- Added M-15 (MSG50 means two things; Q-43). Task map points to `CURRENT_STATE.md` for FE status (D-90).

## 2026-10-03 — first version, `develop` @ `6137e24`

- Added the guide: README, setup, auth, conventions, enums, realtime, module files (auth, user,
  market, watchlist, trading-plan, planned), task map, open questions.
- Endpoints: 35 implemented on `develop`; 6 alert endpoints and the `expectedAlertCount` parameter
  of `DELETE /watchlist/{id}` pending on `feat/t-054-alert-rules` @ `0803903`; 43 planned in TD 8
  plus 13 admin areas.
- Raised FEQ-01…FEQ-05 and recorded mismatches M-01…M-14 in `07-open-questions.md`.
- Placed under `docs/design/fe-guide/` (not `docs/fe-guide/`) because `docs/design/` is already in
  the local-only exclude list of every clone, so the guide cannot show up as untracked in the public
  code repository.
