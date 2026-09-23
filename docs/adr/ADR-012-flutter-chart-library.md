# ADR-012 — Flutter chart library

**Status:** Open
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision —; TECHNICAL_DESIGN section 1.4

## Context
The mobile app must draw candlestick charts with indicator overlays, matching the analysis screens of the web app. The web app uses TradingView Lightweight Charts, which has no first-party Flutter package. Candidates differ in licence, maintenance status, indicator support and performance with 500 candles.

## Decision
Open. To be decided in phase P14, task T-090, before mobile chart work starts. The evaluation must record: licence and attribution obligation, last release date, indicator overlay support, rendering performance with 500 candles on a mid-range Android device, and whether a WebView wrapper around the web chart is acceptable instead.

## Consequences
Deferring is safe because no other mobile task depends on the choice: T-088, T-089, T-091 and T-092 are unaffected. Deciding late is a risk only if the evaluation itself slips, which is tracked as risk R-06.

## Alternatives considered
To be filled in when the decision is made. Include at least one native Flutter package and the WebView option.
