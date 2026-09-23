# ADR-008 — BigDecimal precision and rounding policy

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-08; TECHNICAL_DESIGN section 1.4

## Context
The graded core of the project is financial arithmetic: position size, risk, reward, liquidation price, fees, funding and realized profit. Binary floating point cannot represent decimal prices exactly, so accumulating fees or funding in `double` produces drift that is visible in a demo and impossible to defend (Bloch 2018, Effective Java, Item 60).

## Decision
Prices, quantities, notional values, margins, fees, funding and profit use `BigDecimal` end to end — in entities, in calculators, in the database (`numeric` with the precisions of TECHNICAL_DESIGN 5.4) and in API responses, which serialize them as JSON strings so that JavaScript cannot round them. Divisions use `MathContext.DECIMAL128`; every `setScale` names its `RoundingMode`: quantities down to the step size, prices to the tick size, liquidation distance conservatively. Values are compared with `compareTo`, never `equals`. `double` is permitted only inside indicator mathematics, whose results are display values, never money.

## Consequences
Positive: reproducible arithmetic; results match the exchange calculators used as test oracles; no rounding surprises between backend, web and mobile.

Negative: `BigDecimal` is slower and more verbose than `double`, and the web and mobile clients must use a decimal library instead of native numbers.

Requires: an ArchUnit rule that forbids `double`/`float` fields in entities and in money calculators (CLAUDE.md section 4).

## Alternatives considered
`double` throughout: rejected, accumulation drift.
Integer minor units (`long`): rejected because crypto quantities need eight or more decimal places and the scale differs per pair.
`BigDecimal` internally but JSON numbers on the wire: rejected, JavaScript loses precision on parse.
