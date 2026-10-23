# Changelog — FE integration guide

Newest first. Each entry names the `develop` SHA the guide was synced to.

## 2026-10-23 — TP-A review fixes, branch `feature/TP-A-plan-validity` (on `develop` @ `612b201`)

- `modules/trading-plan.md`: Q-77 answered; a plan on another timeframe than its preset's now gets a
  score; null score cases rewritten; `setupScorePreset` may be null when the read failed.
- `POST /plans/calculate` now answers 400 MSG01 on `invalidationPrice` for a MARKET plan carrying
  one, as create does.

## 2026-10-23 — TP-A plan validity, branch `feature/TP-A-plan-validity` (on `develop` @ `612b201`)

- `modules/trading-plan.md`: every request and response field TP-A adds, from the branch (not merged
  yet): `entryType` `STOP`; `invalidationPrice`, `maxEntryDeviationR`, `analysisTimeframe` in the
  request and the plan; `plannedEntryPrice`; status `INVALIDATED` with `invalidationReason` (plan and
  list row, plus `invalidatedAt` in the row); `setupScoreAtPlan` and `setupScorePreset`, now taken at
  activation from the latest closed candle (Q-74 answered). New section "Plan validity (TP-A)" with the
  rules, the MSG16 and 503 MSG43 cases (every Futures plan with an invalidation price or a Futures
  STOP activation answers 503 MSG43 until TP-0), and the null score cases (Q-77).
- Input rules and the 400/409/503 rows of create, update and activate updated; the
  `CANCELLED_EXPIRED` tab also lists INVALIDATED.
- `04-enums.md`: `STOP`, `INVALIDATED` and the new `InvalidationReason`.

## 2026-10-23 — requests to the backend, `develop` @ `796f408`

- `08-waiting-on-backend.md` rewritten as the list of requests to the backend: defects Q-75
  (notification queue refused by the STOMP guard) and Q-76 (concurrent opening of a moderation case)
  with cause, fix and test; Q-70; admin and TP-A branches to push; FEQ-02, M-09 re-checked; rows
  done since 2026-10-13 (FEQ-01, demo trading, community, notification read API) moved to its
  section 5.
- `07-open-questions.md` section E points to `08`. Only these two files and the T-065 row of
  `06-task-map.md` (D-111 of the web renumbered D-113) were touched; the rest of the guide stays
  synced to `0d92def`.

## 2026-10-08 — re-sync, `develop` @ `0d92def`

- Alerts (T-054, PR #44) and the `expectedAlertCount` check of `DELETE /watchlist/{id}` are on
  `develop`: statuses and sources moved from the branch to `develop`. 41 REST endpoints implemented.
- Alert evaluation: PRICE alerts fire since T-055 (PR #51); INDICATOR alerts are not evaluated (T-110).
- CORS for REST and `/ws` from one list, `CORS_ALLOWED_ORIGINS` (D-83, PR #50): 01-setup and
  05-realtime rewritten; M-02 and M-03 resolved; the proxy is optional.
- `PATCH /watchlist/{id}`: `sortOrder` 0–10000, MSG15 outside.
- 12 moved line references updated (`SecurityConfig`, `WebSocketConfig`, `application.yml`,
  `UpdateWatchlistItemRequest`, `WatchlistController`, `WatchlistServiceImpl`).
- Added M-15 (MSG50 means two things; Q-66). Task map points to `CURRENT_STATE.md` for FE status (D-90).

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
