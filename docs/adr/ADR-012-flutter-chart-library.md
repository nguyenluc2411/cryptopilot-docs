# ADR-012 — Flutter chart library

**Status:** Proposed (FE owner chose option A on 2026-11-07, for the team lead's review)
**Date:** 2026-09-19 (opened); 2026-11-07 (decided by the FE owner)
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE D-144, D-141, D-142, D-126, A-43; TECHNICAL_DESIGN 1.3, 1.4; ADR-016, ADR-023; T-090, T-121, T-122; SRS 3.3.2, 3.3.3, BR-08, BR-14

## Context
The mobile app must draw candlestick charts with indicator overlays, matching the analysis screens of
the web app (SCR-10, SCR-11), and later the paper trading screens (D-142: T-121, T-122) with entry,
stop loss and take profit lines. The web app uses TradingView Lightweight Charts, which has no
first-party Flutter package. Prices are decimal strings in the API and decimals in the app (D-141);
the owner's devices run in Vietnamese, and the web once showed Vietnamese month names on its chart
axes (A-43).

A spike on 2026-11-07 (mobile branch `chore/T-090-chart-spike`, never merged) drew 500 real candles
from `GET /market/spot/{symbol}/candles` with live `/topic/kline.*` updates on the Android emulator of
the mobile process (profile build, software rendering), for three options.

## Decision
**Option A: TradingView Lightweight Charts (the version the web uses, 5.2.1 at the time) bundled as
an asset and drawn in a WebView (`webview_flutter`, Flutter team).** The chart is one neutral
component used by analysis, plans and paper trading alike; it takes candles and price lines with
prices as decimal strings and turns them into numbers only inside the page, to draw.

The following are part of the decision, because the spike measured them:

1. The library and the page are loaded from asset files, never as one inlined HTML string (the
   inlined string crashed the WebView once in the spike and is not kept in the compiled-script cache).
2. One chart page is started early (when the Markets tab opens) and kept; a change of pair or
   timeframe replaces the data, not the page.
3. Candles are fetched while the page starts, not after.
4. The first read asks for the 500 closed candles SRS 3.3.2 names (EMA200 needs that history); older
   ones are read when the Trader reaches the left edge. (Corrected 2026-11-07: the first version of
   this item said about 200, which contradicts the SRS; items 2 and 5 carry the speed.)
5. The last candles of a pair and timeframe are kept on the device and drawn at once, then replaced
   by the fresh ones.
6. The chart's locale is English (`en-US`), never the device default.
7. The licence's attribution is kept: TradingView named as the creator, the attribution notice in the
   app's licences, and the chart's attribution logo, which links to tradingview.com.

## Consequences
With items 1–5 the spike showed candles 0.2–0.6 s after the tap for a pair seen before (from 6.5–6.8 s
without them), the chart page ready in about 30 ms when started early, and about 3.6 s for a pair not
seen before on the emulator, most of it the API call. The chart looks and behaves like the web's,
price lines serve plans (BR-14 levels, entry, stop loss, take profit) and paper trading, realtime
updates are one call per kline, and prices stay decimal strings in the app.

Costs: one more package (`webview_flutter`) and a 198 KB script in the app; a WebView adds about
9 MB of memory per chart page; widget tests cannot draw a WebView, so the chart sits behind an
interface with a test double and is checked on a device. The attribution logo is always shown; it is
a licence condition, not promotion.

Not checked: the measures on a real mid-range Android device (the criterion of this ADR). The FE owner
has no Android device (2026-11-07), so T-090 measures on the emulator only and this criterion stays
open until someone runs the app on a real device (at the latest in the closed testing of T-120). If a
real device then shows the analysis chart later than about 2 s for a pair seen before, this decision
is reviewed. Pinch zoom is checked by hand on the emulator (two-finger mode), not by the test tools.

## Alternatives considered
| | A. Lightweight Charts in a WebView (chosen) | B. `k_chart_plus` 1.0.x (native package) | C. Own `CustomPainter` |
|---|---|---|---|
| Licence | Apache-2.0, attribution required | BSD-style, keep the notice | None |
| Maintenance | TradingView; web uses the same version | One maintainer, 5 releases, last 2025-12-21 | The team |
| Price lines (entry, SL, TP, BR-14 levels) | Yes | No (current price only); needs a fork | Build them |
| Decimal prices | Strings in the app, numbers only to draw | Doubles in the app; computes its own MA/BOLL/MACD/RSI in doubles | Free choice |
| 500 candles, first time (emulator, profile) | 4.6 s untuned; 0.2–0.6 s with items 1–5 for a pair seen before | Immediate | Immediate |
| Look | Same as the web | Its own style, fixed `11-02 23:00` time labels | Any |
| Estimated work | 1.5–2 days for the shared chart | 2–3 days to fork and restyle, still unlike the web | 4–6 days (pan, zoom, crosshair, axes, autoscale, panes) |

B was dropped for the missing price lines and the doubles; C for the cost, with no gain the users
would see over A once A is tuned.
