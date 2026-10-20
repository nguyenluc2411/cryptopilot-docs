# ADR-018 — Web demo trading routes trace to D-86 and stay behind a flag

**Status:** Accepted (FE owner, 2026-10-13)
**Date:** 2026-10-13
**Deciders:** BE1, BE2, FE, DO
**Related:** D-86; paper trading plan sections 5, 16, 17 (TR-F1…F5); ADR-015; CURRENT_STATE D-101; TR-F1

## Context
Every web route traces to an SRS screen id (SCR-01…44), and a test checks that inventory. Demo trading
(D-86) is not in SRS v1.0, so its screens have no SCR id. Its backend module (`/api/v1/paper/**`) is
on the branch `feat/tr-02-paper-trading-schema` and not merged into `develop`; until it is, the web
adapter answers NOT_CONFIGURED (ADR-015). TR-F1 builds the trading layout on the merged market API
now, so the screen exists before the backend module that completes it.

## Decision
Demo trading routes (`/trade/spot`, `/trade/spot/:symbol`, later `/trade/futures/...`) trace to D-86
in place of an SCR id. They and the "Trade" navigation entry are registered only when the build-time
flag `VITE_ENABLE_PAPER_TRADING` is `true`; it stays `false` in production until the backend merges
the paper module, and is turned on then.

## Consequences
The SCR inventory test keeps checking SCR-01…44 only; a separate test checks that every demo trading
route traces to D-86 and that the navigation has no Trade entry without the flag. A production build
never shows a trading screen whose orders cannot be placed. If the SRS later gives these screens SCR
ids, the routes switch to them. Turning the flag on is a configuration change, not a code change.

## Alternatives considered
- Invent SCR ids (SCR-45…): not allowed; ids come from the SRS only.
- Keep the routes always registered with a "not connected" page: shows an unusable screen in
  production and exposes the module before the backend agrees on its contract.
- A runtime flag from system settings (T-082): T-082 is not built; a build flag is enough until then.
