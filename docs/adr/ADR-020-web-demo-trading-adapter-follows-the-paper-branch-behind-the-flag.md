# ADR-020 — Web demo trading adapter follows the backend paper branch behind the flag

**Status:** Proposed
**Date:** 2026-10-13
**Deciders:** BE1, BE2, FE, DO
**Related:** D-86, D-94 (ADR-018); TR-03, TR-04, TR-06, TR-07; TR-F2, TR-F3; ADR-015; CURRENT_STATE D-97

## Context
The web client calls an endpoint only once it is merged; until then its adapter answers NOT_CONFIGURED
(ADR-015). The backend demo trading module (`/api/v1/paper/**`, depth and market trades of TR-03, and
their topics) is DONE on `feat/tr-02-paper-trading-schema` (`f4e66b2`) and not merged into `develop`.
Its screens (TR-F1…F3) already sit behind the build flag `VITE_ENABLE_PAPER_TRADING` (D-94), which stays
`false` in production until the module is merged. With NOT_CONFIGURED adapters, the screens can only be
tried on the development demo exchange, so the module cannot be tested end to end before its merge, and
the merge would be followed by a second FE change to connect it.

## Decision
The web client has HTTP and STOMP adapters for the demo trading module written against the contract of
the backend paper branch (account, wallets, transfers and their history, the ledger, place, cancel and
list orders, fills, depth and market trades with their topics). Every response is decoded as for any
other adapter. They are used only when `VITE_ENABLE_PAPER_TRADING` is `true` and an API base URL is set;
otherwise the services stay NOT_CONFIGURED. Turning the flag on therefore means "this backend has the
paper module", and the flag stays `false` in production until it is merged.

## Consequences
A developer can run the backend paper branch and test the screens with real orders; the merge of the
module needs no FE code change, only the flag. While the branch is unmerged its contract can still
change: the FE re-reads it before the merge (the decoders reject an unexpected shape, so a change shows
as a decode error, not wrong data). A build with the flag on against a backend without the module gets
404s; that is a configuration error.

## Alternatives considered
- Keep NOT_CONFIGURED until the merge (ADR-015 as written): no end-to-end test before the merge and a
  second FE change after it.
- A second flag for the adapters: two switches that must always agree; the screens are useless without
  the adapters.
- Detect the module at runtime (probe `/paper/account`): an extra call on every start and a 404 that
  means two things (no module, no account).
