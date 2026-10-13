# ADR-017 — The web chart computes the indicator series it draws

**Status:** Proposed
**Date:** 2026-10-09
**Deciders:** BE1, BE2, FE, DO
**Related:** SRS 3.3.2, BR-12; TECHNICAL_DESIGN 7.2; D-52, D-55; FEQ-04, M-13; CURRENT_STATE D-96; T-032

## Context
SRS 3.3.2 draws SMA20, EMA20, EMA50, EMA200 and Bollinger Bands over the latest 500 closed candles and
shows Volume with its SMA20, RSI14 and MACD(12,26,9) as panels. `GET /analysis/{market}/{symbol}`
returns the latest value of each indicator only (FEQ-04, M-13); no endpoint returns a series. The
backend computes the indicators incrementally (TECHNICAL_DESIGN 7.2) and keeps one snapshot per
series, so a series endpoint would need new storage or a recomputation per request. T-032 needs the
overlays now; T-033 and T-034 build on the chart.

## Decision
The web client computes the indicator series it draws, in its chart feature, with the definitions and
seeds of BR-12 and TECHNICAL_DESIGN 7.2 as amended by D-52 (MACD seeding, Bollinger deviation) and
D-55 (RSI 50 on a flat seed), using `number` (indicators are not money). It reads 1,000 closed candles
so EMA200 is warmed up as on the server and shows the latest 500. The series are for drawing only:
the analysis card, the setup score and every value a rule acts on come from the backend.

## Consequences
- Overlays and panels work against the existing API; no backend change.
- The formulas exist twice. The client is tested against the backend's golden data (TA-Lib, Binance
  BTCUSDT 1h) within the D-52 tolerance, so a change to BR-12 or to 7.2 must update both and the golden
  data together.
- With fewer than 1,000 candles of history the earliest visible EMA200 values can differ from the
  server's by more than 0.05 %; the last value, which the card shows, comes from the backend anyway.
- Mobile (T-090) needs the same computation in Dart, or the series endpoint below.

## Alternatives considered
- A series endpoint on the backend (indicator values per candle): one source of truth, but new storage
  or a 500-candle recomputation per request, and it was not planned for this sprint. It can replace
  this ADR later without changing the chart's inputs.
- Draw candles only until such an endpoint exists: fails SRS 3.3.2 and delays T-033 and T-034.
