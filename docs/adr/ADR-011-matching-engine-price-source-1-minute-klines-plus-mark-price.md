# ADR-011 — Matching engine price source: 1-minute klines plus mark price

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-11; TECHNICAL_DESIGN section 1.4

## Context
Simulated fills and exits must be defensible: a trader will compare a fill against the real chart. Using only the last trade price of a tick stream misses levels touched between ticks and cannot be replayed after a restart. The SRS recovery rule (NSF-07) proposes 15-minute candles, which is too coarse — a 15-minute candle can contain both the stop loss and the take profit with no way to order them.

## Decision
The engine evaluates entries and exits against the high and low of the `kline_1m` stream and, for futures liquidation, against the mark price stream, as SRS BR-35 requires. After downtime, missing 1-minute klines are fetched by REST and replayed through the same code path as live events. When a stop loss and a take profit fall inside the same candle or replay range, the stop loss is applied first. Alignment item A-04 records the change from the SRS.

## Consequences
Positive: fills match what the trader sees on the chart; replay and live processing share one implementation, so recovery is testable; the conservative tie-break cannot inflate the win rate, which is the statistic the whole journal feature rests on.

Negative: fills are accurate to one minute, not to the tick; the pessimistic tie-break occasionally reports a loss where reality might have given a win.

Requires: 1-minute klines are ingested and retained for every enabled pair, and the replay test asserts that replay equals live processing.

## Alternatives considered
Tick stream only: rejected, no replay after downtime and levels between ticks are missed.
15-minute candles for recovery as written in the SRS: rejected, cannot order two levels inside one candle.
Aggregate trade stream: rejected, the volume and storage cost is not repaid by the extra precision at this scale.
