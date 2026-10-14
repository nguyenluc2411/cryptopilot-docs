# Changelog — FE integration guide

Newest first. Each entry names the `develop` SHA the guide was synced to.

## 2026-10-14 — FEQ-01 pair id, `develop` @ `233fcc8`

- Backend `fix/feq-01-pair-id` (`5ef54e1`, pushed, PR to open): each row of `GET /market/pairs`
  carries `pairId`, the id the watchlist, alert, plan and demo order requests take. Additive.
- FE `fix/FEQ-01-pair-id` (`799753d`, pushed, PR to open): `MarketPair.pairId` decoded (optional,
  so an older backend still decodes); the demo Spot screen and the Orders pair filter take it, with
  the watchlist row as fallback.
- Still open under FEQ-01 on FE: Add to watchlist, Create plan and Create alert from SCR-10/11,
  the pair name in plan rows (resolve from the pair list).

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
