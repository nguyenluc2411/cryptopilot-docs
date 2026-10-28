# Module: market

Screens SCR-01 (public home), SCR-09 (market list), SCR-10 (Spot analysis), SCR-11 (Futures analysis).
Realtime: [../05-realtime.md](../05-realtime.md).
Code prefix: `backend/src/main/java/com/cryptopilot/market/`.

Common rules of `/market/**`:

- Public (Guest). No token needed; a valid token is accepted — and read for the plan on the two
  Futures endpoints below.
- `{market}` / `?market=`: `spot` or `futures`, any case. Responses spell it `SPOT` / `FUTURES`.
- `{symbol}`: any case, e.g. `btcusdt`; responses upper case.
- A pair that is not enabled on that market (BR-07) → 404 MSG41.
- A bad parameter (market, tf, limit, range, page) → 400 MSG01 **without** an `errors` map.
- **D-60 plan gates (T-107, branch `feat/t-107-analysis-gates`, not merged yet):**
  `GET /market/futures/{symbol}/metrics` needs a token (401 MSG44) and a plan with
  `FUTURES_ANALYSIS` (403 MSG29, PRO and PREMIUM); `GET /market/futures/{symbol}/stats` stays public
  but answers `openInterest`, `longShortRatio` and `lastFundingSettlement` only to PRO and PREMIUM —
  `null` for a Guest or FREE. Send the token on both when the user is signed in.

---

### GET /market/pairs
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Pairs enabled on a market, in admin display order (SCR-01, SCR-09).

| Query | Type | Required | Rule |
|---|---|---|---|
| `market` | `spot` \| `futures` | yes | missing → MSG01 `errors.market` "is required"; other value → MSG01 |
| `page` | int | no | ≥ 1, default 1 |
| `pageSize` | int | no | 1–100, default 20 |

Response `200` — `PageResponse<PairResponse>`:

```json
{
  "items": [
    {
      "symbol": "BTCUSDT",
      "market": "SPOT",
      "baseAsset": "BTC",
      "quoteAsset": "USDT",
      "baseAssetName": "Bitcoin",
      "logoUrl": null,
      "tickSize": "0.01",
      "stepSize": "0.00001",
      "minNotional": "5",
      "displayOrder": 1
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 13
}
```

```ts
interface PairResponse {
  symbol: string;
  market: 'SPOT' | 'FUTURES';
  baseAsset: string | null;
  quoteAsset: string | null;
  baseAssetName: string | null;
  logoUrl: string | null;
  tickSize: string | null;     // price precision (CR-02)
  stepSize: string | null;     // quantity precision
  minNotional: string | null;
  displayOrder: number;
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Bad `market`, `page`, `pageSize` |

FE notes:
- **No pair `id` in the response.** `POST /watchlist`, `POST /plans` and `POST /alerts` need a
  `pairId` (UUID); no implemented endpoint returns a pair's id for a symbol. Blocks "Add to
  Watchlist" / "Create Trading Plan" from market screens (FEQ-01, M-01).
- No prices here: combine with `/topic/overview.{MARKET}` (or `…/stats` per pair while Delayed).
- No search or sort parameters: 13–50 pairs, fetch `pageSize=100` once and sort/search on the client
  (SRS 3.3.1).
- Cache for minutes; the list changes only when an admin enables/disables a pair.
Source: `market/controller/MarketController.java#L51`; `market/dto/response/PairResponse.java#L21`. Spec: SRS 3.3.1, UC-09, BR-07, D-49.

---

### GET /market/{market}/{symbol}/candles
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Closed candles of one series, oldest first (charts).

| Param | In | Type | Required | Rule |
|---|---|---|---|---|
| `market` | path | `spot` \| `futures` | yes | |
| `symbol` | path | string | yes | enabled on that market, else 404 |
| `tf` | query | `15m` \| `1h` \| `4h` \| `1d` | yes | exact code |
| `limit` | query | int | no | 1–1000, default 500 |
| `from` | query | ISO instant | no | inclusive; `[from, to)` must hold ≤ 1000 candles of `tf` |
| `to` | query | ISO instant | no | exclusive; default now; not in the future |

Returns the **newest** `limit` closed candles opened in `[from, to)`, sorted oldest first. Page
backwards by passing the first `openTime` as the next `to`.

Response `200`:

```json
{
  "symbol": "BTCUSDT",
  "market": "SPOT",
  "timeframe": "1h",
  "candles": [
    {
      "openTime": "2026-10-03T01:00:00Z",
      "closeTime": "2026-10-03T01:59:59.999Z",
      "open": "62950.00", "high": "63100.00", "low": "62900.10", "close": "63010.55",
      "baseVolume": "812.33", "quoteVolume": "51190021.77", "tradeCount": 40211
    }
  ]
}
```

```ts
interface CandlesResponse { symbol: string; market: 'SPOT' | 'FUTURES'; timeframe: string; candles: Candle[] }
interface Candle {
  openTime: string; closeTime: string;
  open: string; high: string; low: string; close: string;
  baseVolume: string; quoteVolume: string;
  tradeCount: number | null;
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Bad `market`/`tf`/`limit`, `to` in the future, `from` ≥ `to`, range > 1000 candles |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Pair not enabled on that market |

FE notes: the forming candle is not here — it comes from `/topic/kline.*` (`closed: false`). SCR-10
default: `tf=1h`, `limit=500`. SCR-01 basic chart: `tf=1d`, `limit=90` (SRS 3.3.1). Cache per
(market, symbol, tf); refetch after a reconnect (gap fill).
Source: `market/controller/MarketController.java#L66`; `market/dto/response/CandlesResponse.java#L16`; `market/dto/response/CandleResponse.java#L21`. Spec: UC-09, BR-08, D-49.

---

### GET /market/spot/{symbol}/stats
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Latest stored Spot ticker of a pair (SCR-10 statistics; fallback while Delayed).

Response `200`:

```json
{
  "symbol": "BTCUSDT",
  "serverTime": "2026-10-03T02:15:30Z",
  "ticker": {
    "asOf": "2026-10-03T02:15:00Z",
    "lastPrice": "63000.01", "bestBid": "63000.00", "bestAsk": "63000.01",
    "high24h": "63950.00", "low24h": "61820.50", "changePercent24h": "1.254",
    "baseVolume24h": "18234.11", "quoteVolume24h": "1139455120.42"
  }
}
```

```ts
interface SpotStatsResponse { symbol: string; serverTime: string; ticker: SpotTicker | null }
interface SpotTicker {
  asOf: string;
  lastPrice: string | null; bestBid: string | null; bestAsk: string | null;
  high24h: string | null; low24h: string | null; changePercent24h: string | null;
  baseVolume24h: string | null; quoteVolume24h: string | null;
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not enabled on Spot |

FE notes: values are the stored once-a-minute snapshot (`asOf`), up to ~1 min old; live values come
from the ticker topic. `ticker` is `null` until a snapshot exists. Spread = `bestAsk − bestBid`
(compute with a decimal library).
Source: `market/controller/MarketController.java#L88`; `market/dto/response/SpotStatsResponse.java#L14`; `market/dto/response/SpotTickerResponse.java#L21`. Spec: SRS 3.3.2, D-49.

---

### GET /market/futures/{symbol}/stats
Status: IMPLEMENTED (develop); plan gate on branch `feat/t-107-analysis-gates`
Auth: public; send the token when signed in — the blocks after `price` need `FUTURES_ANALYSIS` (D-60)
Purpose: Latest mark price, funding, open interest, long/short ratio and last settlement (SCR-11).

Response `200`:

```json
{
  "symbol": "BTCUSDT",
  "serverTime": "2026-10-03T02:15:30Z",
  "price": {
    "asOf": "2026-10-03T02:15:00Z",
    "markPrice": "63010.20", "indexPrice": "63005.80",
    "fundingRate": "0.00010000", "nextFundingTime": "2026-10-03T08:00:00Z"
  },
  "openInterest": { "time": "2026-10-03T02:10:00Z", "openInterest": "81234.512", "openInterestValue": "5118221330.10" },
  "longShortRatio": { "time": "2026-10-03T02:10:00Z", "longShortRatio": "1.8421", "longAccountRatio": "0.6481", "shortAccountRatio": "0.3519" },
  "lastFundingSettlement": { "fundingTime": "2026-10-03T00:00:00Z", "fundingRate": "0.00008210", "markPrice": "62880.00" }
}
```

```ts
interface FuturesStatsResponse {
  symbol: string;
  serverTime: string;
  price: { asOf: string; markPrice: string | null; indexPrice: string | null; fundingRate: string | null; nextFundingTime: string | null } | null;
  openInterest: OpenInterest | null;
  longShortRatio: LongShortRatio | null;
  lastFundingSettlement: FundingSettlement | null;
}
interface OpenInterest { time: string; openInterest: string; openInterestValue: string | null }
interface LongShortRatio { time: string; longShortRatio: string; longAccountRatio: string; shortAccountRatio: string }
interface FundingSettlement { fundingTime: string; fundingRate: string; markPrice: string | null }
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not enabled on Futures |

FE notes: each block has its own instant and is `null` until stored. **For a Guest or a FREE Trader
`openInterest`, `longShortRatio` and `lastFundingSettlement` are always `null`** (D-60): the plan
does not include them, nothing is wrong with the data. Only SCR-11 shows those blocks, and SCR-11 is
gated by `GET /analysis/futures/…` (403 MSG29 on FREE), so a screen that got its analysis also gets
the blocks. Funding countdown: from
`price.nextFundingTime` (live from the ticker topic), never assume 8 h (BR-11). **No last price and
no 24h statistics for Futures** (M-09).
Source: `market/controller/MarketController.java#L101`; `market/dto/response/FuturesStatsResponse.java#L22`; `market/dto/response/FuturesPriceResponse.java#L20`. Spec: SRS 3.3.3, BR-10, BR-11, D-45, D-60.

---

### GET /market/futures/{symbol}/metrics
Status: IMPLEMENTED (develop); plan gate on branch `feat/t-107-analysis-gates`
Auth: trader with `FUTURES_ANALYSIS` (PRO, PREMIUM) — the path is public, the gate is the plan (D-60)
Purpose: Open interest, long/short ratio and settled funding series over a range (SCR-11 charts).

| Query | Type | Required | Rule |
|---|---|---|---|
| `from` | ISO instant | no | default `to − 1 day`; inclusive |
| `to` | ISO instant | no | default now; not in the future |
| | | | `from < to`, range ≤ 7 days |

Response `200`:

```json
{
  "symbol": "BTCUSDT",
  "from": "2026-10-02T02:15:30Z",
  "to": "2026-10-03T02:15:30Z",
  "openInterest": [ { "time": "2026-10-02T02:20:00Z", "openInterest": "80911.004", "openInterestValue": "5090112003.55" } ],
  "longShortRatio": [ { "time": "2026-10-02T02:20:00Z", "longShortRatio": "1.7712", "longAccountRatio": "0.6391", "shortAccountRatio": "0.3609" } ],
  "fundingSettlements": [ { "fundingTime": "2026-10-02T08:00:00Z", "fundingRate": "0.00010000", "markPrice": "62411.00" } ],
  "availableFrom": { "openInterest": "2026-09-03T00:00:00Z", "longShortRatio": "2026-09-03T00:00:00Z", "fundingSettlements": "2026-09-03T00:00:00Z" }
}
```

```ts
interface FuturesMetricsResponse {
  symbol: string; from: string; to: string;
  openInterest: OpenInterest[];        // 5-minute points, sparse
  longShortRatio: LongShortRatio[];    // 5-minute points, sparse
  fundingSettlements: FundingSettlement[];
  availableFrom: { openInterest: string | null; longShortRatio: string | null; fundingSettlements: string | null };
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | `to` in future, `from ≥ to`, range > 7 days |
| 401 | `AUTHENTICATION_REQUIRED` | MSG44 | No token (checked first) |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | FREE plan (checked before the range); upgrade prompt |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not enabled on Futures |

FE notes: series are sparse — do not assume a point every 5 minutes. When `availableFrom` is after
`from`, state the available period on the chart (SRS 3.3.3). Refresh every 5 minutes at most (NSF-04
cadence).
Source: `market/controller/MarketController.java#L113`; `market/dto/response/FuturesMetricsResponse.java#L21`. Spec: SRS 3.3.3, BR-10, D-45, D-49.

---

### GET /analysis/{market}/{symbol}
Status: IMPLEMENTED (develop); plan gates and `componentsLocked` on branch `feat/t-107-analysis-gates`
Auth: trader; Futures needs `FUTURES_ANALYSIS`, the component scores need `SCORE_COMPONENTS` (D-60)
Purpose: Latest indicators, support/resistance and setup score of a pair (SCR-10, SCR-11; UC-10, UC-11).

| Param | In | Type | Required | Rule |
|---|---|---|---|---|
| `market` | path | `spot` \| `futures` | yes | |
| `symbol` | path | string | yes | enabled on that market |
| `tf` | query | `15m` \| `1h` \| `4h` \| `1d` | no | default `1h`; empty or other → MSG01 |

Response `200` (Futures shown; Spot has no `derivatives` and no `dominantSide` keys):

```json
{
  "symbol": "BTCUSDT",
  "market": "FUTURES",
  "timeframe": "1h",
  "openTime": "2026-10-03T01:00:00Z",
  "calculatedAt": "2026-10-03T02:00:03.412Z",
  "indicators": {
    "sma20": "62711.1250000000", "ema20": "62790.4410000000", "ema50": "62402.0090000000", "ema200": "60120.7700000000",
    "rsi14": "61.2045000000",
    "macdLine": "141.2200000000", "macdSignal": "120.0100000000", "macdHistogram": "21.2100000000",
    "bbUpper": "63420.0000000000", "bbMiddle": "62711.1250000000", "bbLower": "62002.2500000000",
    "volumeSma20": "790.1200000000"
  },
  "nearestSupport": "62400.00",
  "nearestResistance": "63500.00",
  "componentsLocked": false,
  "components": { "formulaVersion": "v1", "trend": "75.00", "momentum": "60.00", "volume": "55.00", "level": "40.00", "derivatives": "50.00" },
  "setupScore": {
    "score": 62,
    "preset": "DAY_TRADING",
    "presetVersion": "v1",
    "timeframe": "1h",
    "openTime": "2026-10-03T01:00:00Z",
    "components": { "formulaVersion": "v1", "trend": "75.00", "momentum": "60.00", "volume": "55.00", "level": "40.00", "derivatives": "50.00" },
    "dominantSide": "LONG"
  }
}
```

```ts
interface AnalysisResponse {
  symbol: string;
  market: 'SPOT' | 'FUTURES';
  timeframe: string;              // the requested tf
  openTime: string | null;        // candle the indicators belong to; null = no data yet
  calculatedAt: string | null;
  indicators: Indicators;         // every value string | null
  nearestSupport: string | null;
  nearestResistance: string | null;
  componentsLocked: boolean;      // true = plan lacks SCORE_COMPONENTS (FREE): both component blocks null
  components: Components | null;  // of the requested tf; null only when componentsLocked
  setupScore: SetupScore;         // read on the PRESET's timeframe, not tf
}
interface Indicators {
  sma20: string | null; ema20: string | null; ema50: string | null; ema200: string | null;
  rsi14: string | null; macdLine: string | null; macdSignal: string | null; macdHistogram: string | null;
  bbUpper: string | null; bbMiddle: string | null; bbLower: string | null; volumeSma20: string | null;
}
interface Components {           // 0–100 each, or null
  formulaVersion: string | null;
  trend: string | null; momentum: string | null; volume: string | null; level: string | null;
  derivatives?: string | null;   // FUTURES only
}
interface SetupScore {
  score: number | null;          // 0–100 integer; null = insufficient data
  preset: 'SCALPING' | 'DAY_TRADING' | 'SWING';
  presetVersion: string;
  timeframe: string;             // preset timeframe: 15m / 1h / 4h
  openTime: string | null;
  components: Components | null;  // null only when componentsLocked
  dominantSide?: 'LONG' | 'SHORT' | 'NEUTRAL' | null; // FUTURES only
}
```

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Bad `market` or `tf` | Banner |
| 401 | `AUTHENTICATION_REQUIRED` | MSG44 | No session (Guests cannot call this) | Login prompt |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | `futures` on FREE (checked after `market`/`tf`, before the pair) | Lock + upgrade prompt (CR-08) |
| 403 | `ACCESS_DENIED` | MSG43 | ADMIN token | — |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not enabled on that market | "Pair no longer available", back to SCR-09 |

FE notes:
- `null` anywhere = "Insufficient data" (fewer than 200 closed candles), never 0 (SRS 3.3.2).
- The score's `timeframe` is the preset's (from the Trader's trading style), and can differ from the
  chart's `tf`. Show preset name + version and the MSG42 disclaimer on the card (D-53, BR-60).
- Re-fetch when a message arrives on `/topic/analysis.{MARKET}.{SYMBOL}.{tf}` (D-126, branch `feat/t-029-analysis-push`); until that branch is merged, when a `closed: true` kline of the same series arrives.
  Values update about 10 s after the candle close (NSF-05).
- FREE plan (D-60, CR-08): Spot answers 200 with `componentsLocked: true`, `components: null` and
  `setupScore.components: null`; the total `score`, `preset`, `presetVersion`, indicators and levels
  are still there. Show the component rows with a lock icon that opens the upgrade prompt (MSG29) —
  **do not** show "Insufficient data" for them: read `componentsLocked` before the null rule. Futures
  answers 403 MSG29 as a whole. PRO and PREMIUM: `componentsLocked: false`, as before.
Source: `market/controller/AnalysisController.java#L50`; `market/dto/response/AnalysisResponse.java#L24`; `market/dto/response/IndicatorsResponse.java#L24`; `market/dto/response/SpotSetupScoreResponse.java#L19`; `market/dto/response/FuturesSetupScoreResponse.java#L21`; `market/dto/response/SpotComponentsResponse.java#L16`; `market/dto/response/FuturesComponentsResponse.java#L18`. Spec: SRS 3.3.2, 3.3.3, UC-10, UC-11, BR-12…BR-14, D-53, D-60, Q-21.
