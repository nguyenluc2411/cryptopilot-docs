# Changelog — FE integration guide

Newest first. Each entry names the `develop` SHA the guide was synced to.

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
