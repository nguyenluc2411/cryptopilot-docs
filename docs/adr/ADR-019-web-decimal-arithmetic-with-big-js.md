# ADR-019 — Web decimal arithmetic with big.js

**Status:** Accepted (FE owner, 2026-10-13)
**Date:** 2026-10-13
**Deciders:** BE1, BE2, FE, DO
**Related:** TECHNICAL_DESIGN 1.3, 5.4 (ADR-008); ADR-016; D-86, paper trading plan sections 6, 7, 13, 16; fe-guide conventions (decimals as strings); CURRENT_STATE D-102; TR-F3, TR-F4, TR-F5

## Context
Every price, quantity and amount reaches the web client as a decimal string (TECHNICAL_DESIGN 5.4) and
must never become a `number`. Until now the client only formats, compares and subtracts such strings
(display only). The demo trading forms (TR-F3, TR-F4) must compute before the order is sent: notional
= price × quantity, quantity from a percentage of the free balance, the estimated fee, the VWAP of a
Market order over depth20, rounding a price down to the tick and a quantity down to the step, and later
uPnL from the mark price and margin figures (plan sections 6, 7 and 13). The backend decides every
order; the client values are estimates shown before confirmation. Writing multiplication, division and
rounding modes on strings by hand is error-prone, and ADR-016 allows no library beyond the listed ones
without an ADR. The paper trading plan (section 16) suggests `decimal.js`.

## Decision
The web client does decimal arithmetic with `big.js` (MIT, exact version pinned when TR-F3 adds it),
through one module `utils/decimal-math.ts` that takes and returns strings: add, subtract, multiply,
divide with a fixed number of fraction digits, compare, and round to a tick or step with an explicit
mode (down for quantities and Buy prices, up for Sell prices, half-up for display). It creates its own
`Big` constructor (`Big()`), so the global settings are never changed: 18 fraction digits for division
and round-down by default. Components and hooks use that module, never `Big` directly; values stay
strings in the domain model and in requests. Indicators keep using `number` (D-103).

## Consequences
Exact results for the operations a trading form needs, matching `BigDecimal` for the same inputs and
rounding modes, covered by the test vectors of plan section 13. The library is small (about 6 KB
minified) and loaded with the trading screens only. Functions that `big.js` lacks (logarithms,
powers with decimal exponents) are not available; if a later screen needs them, this ADR is revisited.
The scale of each kind (TECHNICAL_DESIGN 5.4: price and quantity 12, USDT 8) is applied by the module,
not by callers.

## Alternatives considered
- `decimal.js` (plan section 16): covers the same operations and more (trigonometry, exponentials),
  but the package is about five times larger and nothing on the roadmap needs the extra functions.
- `bignumber.js`: similar to `decimal.js` in size and features; same reason.
- Hand-written string arithmetic on `BigInt`: no dependency, but multiplication, division and every
  rounding mode would be ours to test and maintain.
- `number` with rounding on display: loses precision on small steps and large notionals; ruled out by
  TECHNICAL_DESIGN 5.4.
