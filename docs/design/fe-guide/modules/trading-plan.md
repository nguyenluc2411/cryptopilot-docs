# Module: trading (trading plans)

Screens SCR-16 (plan list), SCR-17 (create/edit with live risk panel), SCR-18 (plan detail),
SCR-19 (close position, planned). All endpoints: TRADER only.
Code prefix: `backend/src/main/java/com/cryptopilot/trading/`. Controller: `controller/TradingPlanController.java`.

Read first:

- **Futures plans cannot be sized in any environment today.** No leverage brackets are stored (they
  need the admin screen, T-085), so every `market: "FUTURES"` calculate/create/activate answers 400
  `errors.leverage` MSG15 (D-70). FREE users get 403 MSG29 first.
- No fills yet (matching engine T-042+): an ACTIVE plan, MARKET included, stays ACTIVE. `EXECUTED`,
  `EXPIRED`, the live position block and close-position do not exist yet.
- Plan responses carry `pairId` but **no symbol** (FEQ-01).
- **Plan validity (TP-A, D-111, D-112), branch `feature/TP-A-plan-validity`, not on `develop` yet:**
  STOP entry, invalidation price, own entry deviation limit, analysis timeframe, the INVALIDATED status
  and the setup score taken at activation. See "Plan validity (TP-A)" below. A STOP plan can be
  activated but never triggers until the engine handles it (TP-B), so **keep STOP hidden in the web
  until TP-B**; nothing becomes INVALIDATED until TP-B either.
- **Fees in the risk panel (TP-0, D-116), branch `feat/tp-0-realism`, not on `develop` yet:** the
  snapshot carries seven fee figures and a ninth warning `HIGH_FEE_SHARE`. See "Fees and slippage in
  the risk panel (TP-0)" below. Futures MARKET plans are now priced at the Futures **last** price.

## Shared types

```ts
interface PlanInputs {
  market: 'SPOT' | 'FUTURES';
  direction: 'LONG' | 'SHORT';        // SPOT: LONG only
  entryType: 'LIMIT' | 'MARKET' | 'STOP';   // STOP: TP-A
  entryPrice?: string | null;         // LIMIT and STOP (the stop price): required; MARKET: ignored
  stopLoss: string;
  takeProfit: string;
  capital?: string | null;            // default: profile defaultCapital
  riskPercent?: string | null;        // default: profile defaultRiskPercent, else risk profile's risk per trade
  leverage?: number | null;           // default 1; SPOT must be 1 or absent
  expiresAt?: string | null;          // LIMIT and STOP default now + 7 days
  note?: string | null;
  invalidationPrice?: string | null;  // TP-A; LIMIT and STOP only; see "Plan validity"
  maxEntryDeviationR?: string | null; // TP-A; > 0 and <= ENTRY_DEVIATION_BLOCK_R (0.75)
  analysisTimeframe?: '15m' | '1h' | '4h' | '1d' | null;  // TP-A; default from the trading style
  activate?: boolean | null;          // true = "Save and Activate"
}
interface CreateTradingPlanRequest extends PlanInputs { pairId: string }
type UpdateTradingPlanRequest = PlanInputs;   // the pair cannot change

interface PlanSnapshot {
  positionQuantity: string;
  notionalValue: string;
  initialMargin: string;
  maintenanceMarginRateUsed: string | null;   // FUTURES
  riskAmount: string;
  rewardAmount: string;
  riskRewardRatio: string;
  estimatedLiquidationPrice: string | null;   // FUTURES
  // TP-0 (D-116): expected costs; null on a plan saved before TP-0. Funding and the liquidation
  // clearance fee are NOT included.
  estimatedEntryFee: string | null;           // entry notional x fee rate of the expected role
  estimatedStopLossExitFee: string | null;    // taker x quantity x stop loss
  estimatedTakeProfitExitFee: string | null;  // maker x quantity x take profit
  estimatedSlippage: string | null;           // SLIPPAGE_BPS on the taker legs, in quote currency
  lossAtStopLoss: string | null;              // "Real loss at stop loss"
  feeShareOfRisk: string | null;              // (lossAtStopLoss - riskAmount) / riskAmount, e.g. "0.19950000"
  netRiskReward: string | null;               // "R:R after fees"
}
interface PlanWarning {
  type: WarningType;                  // see 04-enums
  severity: 'INFO' | 'WARNING' | 'BLOCKING';
  message: string;                    // developer English; build UI text from `type`
}
interface PlanCalculationResponse {
  entryPrice: string;                 // after tick rounding; MARKET: current last price (the reference price)
  expectedFillPrice: string | null;   // TP-0, MARKET only: entryPrice moved by SLIPPAGE_BPS against the Trader;
                                      // the price the quantity is sized on and fills at; = entryPrice at 0 bps
  capital: string;                    // after defaults
  riskPercent: string;                // after defaults
  snapshot: PlanSnapshot;
  warnings: PlanWarning[];
  blocksActivation: boolean;          // true when any BLOCKING warning
}
interface TradingPlanResponse {
  id: string;
  pairId: string;
  market: 'SPOT' | 'FUTURES';
  direction: 'LONG' | 'SHORT';
  entryType: 'LIMIT' | 'MARKET' | 'STOP';
  entryPrice: string;                 // MARKET: the reference price (= plannedEntryPrice), as in /plans/calculate
  expectedFillPrice: string | null;   // TP-0, MARKET only: the price the quantity was sized on; null LIMIT/STOP
  plannedEntryPrice: string | null;   // TP-A; entered price (LIMIT, STOP), reference price of the last save (MARKET)
  stopLoss: string;
  takeProfit: string;
  capital: string;
  riskPercent: string;
  leverage: number | null;          // null on SPOT
  marginMode: 'ISOLATED' | null;
  expiresAt: string | null;
  note: string | null;
  invalidationPrice: string | null;   // TP-A
  maxEntryDeviationR: string | null;  // TP-A
  analysisTimeframe: '15m' | '1h' | '4h' | '1d';  // TP-A; always set
  status: 'DRAFT' | 'ACTIVE' | 'EXECUTED' | 'CANCELLED' | 'EXPIRED' | 'INVALIDATED';
  invalidationReason: InvalidationReason | null;  // TP-A; set only with INVALIDATED
  setupScoreAtPlan: string | null;    // TP-A; 0-100 at scale 2, e.g. "59.00"; null before activation or when unreadable
  setupScorePreset: string | null;    // TP-A; e.g. "DAY_TRADING v1"; set at activation, null before
  editable: boolean;                  // true only for DRAFT
  snapshot: PlanSnapshot;
  warnings: PlanWarning[];
  blocksActivation: boolean;
  statusHistory: { status: PlanStatus; at: string }[];  // oldest first, from the status instants
}
interface TradingPlanSummary {
  id: string; pairId: string;
  market: 'SPOT' | 'FUTURES'; direction: 'LONG' | 'SHORT'; entryType: 'LIMIT' | 'MARKET' | 'STOP';
  entryPrice: string; stopLoss: string; takeProfit: string;   // entryPrice as in the detail
  expectedFillPrice: string | null; // TP-0, MARKET only; null for LIMIT and STOP
  leverage: number | null;          // null on SPOT
  riskAmount: string; riskRewardRatio: string;
  status: PlanStatus;
  createdAt: string; activatedAt: string | null; expiresAt: string | null;
  invalidatedAt: string | null;       // TP-A
  invalidationReason: InvalidationReason | null;  // TP-A
}
type InvalidationReason = 'TAKE_PROFIT_REACHED' | 'STOP_LOSS_REACHED' | 'INVALIDATION_PRICE';
```

## Fees and slippage in the risk panel (TP-0)

Status: on `feat/tp-0-realism` (stacked on TP-A and T-045, not merged). Spec: BR-23, BR-29, BR-31,
BR-36; D-111 E1/E2/E3/E5, D-112 R6, D-116.

- **The quantity does not change.** It is still risk budget / |entry − stop loss| (BR-23). The new
  figures show what fees and slippage add to that risk; nothing is re-sized for them.
- **Show next to the existing figures** (calculate panel, create/edit, plan detail):
  - "Real loss at stop loss" = `lossAtStopLoss`, next to "Risk amount" (`riskAmount`);
  - "R:R after fees" = `netRiskReward`, next to "R:R" (`riskRewardRatio`);
  - optionally the breakdown `estimatedEntryFee`, `estimatedStopLossExitFee`,
    `estimatedTakeProfitExitFee`, `estimatedSlippage`, and `feeShareOfRisk` as a percentage.
  - Tooltip on both: "Includes the trading fees of the entry and of the exit at the stop loss (or
    the take profit, for R:R after fees) and the configured slippage. Funding and the liquidation
    fee are not included."
- **Which fee rate.** By the expected liquidity role: MARKET and STOP entries, and a LIMIT the
  current last price already reaches, pay **taker**; a LIMIT that rests pays **maker**. The stop
  loss exit is taker, the take profit exit maker. A LIMIT's role can change between two panel calls
  when the last price moves across the limit; read the figures from each response, never compute
  them on the client.
- **MARKET entry with slippage.** In `POST /plans/calculate`, `entryPrice` of a MARKET plan stays the
  current last price (the reference price) and `expectedFillPrice` beside it is that price moved by
  `SLIPPAGE_BPS` against the Trader (a buy up, a sell down, rounded to the tick against them). The
  quantity is sized on `expectedFillPrice`, and the activation fills there. `SLIPPAGE_BPS` is 0 today,
  so the two are equal; show "Expected fill" next to the price only when they differ. LIMIT and STOP
  answer `expectedFillPrice: null`. **Both fields mean the same in every response** — calculate,
  create, update, activate, detail and list: `entryPrice` is the reference price (a saved plan's
  `plannedEntryPrice`, from its last draft save) and `expectedFillPrice` the price the quantity was
  sized on. After an activation, `expectedFillPrice` is the price of the activation's recalculation
  and `entryPrice` stays the planned entry; the difference is the entry deviation (TP-C). A MARKET
  plan filled before TP-A has no planned entry: both fields then show the fill. A LIMIT filled at
  activation fills at the last price with slippage, never past its limit.
- **Futures MARKET** is priced and filled at the Futures last price (before: the mark price). The
  mark price stays for the liquidation price and unrealized P/L.
- **New warning `HIGH_FEE_SHARE`** (WARNING, never blocks activation): `feeShareOfRisk` at or above
  `FEE_RISK_WARN_RATIO` (0.20). Suggested text: "Fees and slippage are {feeShareOfRisk × 100}% of
  your risk". See 04-enums.
- Plans saved before TP-0 answer `null` for all seven figures; show "—".
- Example (Futures LONG MARKET, entry 100,000, SL 99,500, TP 101,500, risk 100 USDT):
  `riskAmount` "100.00000000", `estimatedEntryFee` "10.00000000", `estimatedStopLossExitFee`
  "9.95000000", `estimatedTakeProfitExitFee` "4.06000000", `estimatedSlippage` "0.00000000",
  `lossAtStopLoss` "119.95000000", `feeShareOfRisk` "0.19950000" (no warning), `netRiskReward`
  "2.38382659" (R:R 3.0 before fees).

## Input rules (request validation, 400 with `errors`)

| Field | Rule → MSG |
|---|---|
| `pairId`, `market`, `direction`, `entryType`, `stopLoss`, `takeProfit` | required → MSG01 |
| `entryPrice`, `stopLoss`, `takeProfit` | > 0, ≤ 16 integer / 12 decimal digits → MSG15; rounded to the tick (half-up) before checks |
| `capital` | > 0, ≤ 20 / 8 digits → MSG15; absent and no profile default → MSG01 `errors.capital` |
| `riskPercent` | 0.1–10, ≤ 3 decimals → MSG15 |
| `leverage` | ≥ 1 → MSG15; SPOT with leverage ≠ 1 → MSG01 |
| `direction` | SPOT with SHORT → MSG01 |
| `entryPrice` | LIMIT or STOP without it → MSG01 |
| `invalidationPrice` | TP-A. MARKET with a value → MSG01; on the wrong side of the current last price → MSG16 (see "Plan validity"); rounded to the tick |
| `maxEntryDeviationR` | TP-A. ≤ 0, or above `ENTRY_DEVIATION_BLOCK_R` (0.75) → MSG15 |
| `analysisTimeframe` | TP-A. Not one of `15m`, `1h`, `4h`, `1d` → MSG15 |
| `note` | ≤ 1000 → MSG15 |
| `expiresAt` | must be after the activation instant → 400 MSG01 (no `errors` map) |

Calculation rejections (400, `errors`):

| Key | MSG | Meaning |
|---|---|---|
| `stopLoss` / `takeProfit` | MSG16 | Wrong side of the entry for the direction (BR-22): LONG `SL < entry < TP`, SHORT `TP < entry < SL` |
| `quantity` | MSG15 | Risk budget buys less than one step |
| `notional` | MSG15 | Below the pair's `minNotional`, or above the largest leverage bracket |
| `leverage` | MSG15 | No leverage brackets for the pair, or above the bracket maximum |

Client-side mirror for SCR-17 (CR-05): check required fields, ranges and price order before calling
`/calculate`, and fill MSG15/MSG16 placeholders yourself (`{min}`, `{max}`, `{direction}`, `{rule}`).

## Plan validity (TP-A)

Status: on `feature/TP-A-plan-validity` (not merged). Spec: BR-33, BR-68, BR-69, BR-70; D-111, D-112.

- **STOP entry.** A stop-market entry for breakouts: `entryPrice` is the stop price. LONG triggers
  when the last price is ≥ the stop, SHORT when ≤. Without an expiry it gets 7 days, as LIMIT.
  Activating (Activate or Save and Activate) a STOP the last price has already reached answers 400
  `errors.entryPrice` MSG16; it is never turned into MARKET — offer MARKET to the Trader. Until TP-B,
  an activated STOP stays ACTIVE and never triggers: the engine does not trigger STOP entries yet.
  **The web keeps STOP hidden until TP-B** (do not offer it in the entry type selector); the API
  already accepts it, so a STOP plan made through the API alone is still listed and shown.
- **`invalidationPrice`** (LIMIT and STOP only). It must lie on the far side of the current last
  price from the entry, so the price can reach it before the entry: LONG LIMIT with last 102, entry
  100 → invalidation above 102. Checked at save and again at activation; wrong side → 400
  `errors.invalidationPrice` MSG16. Equal to the last price counts as the wrong side.
- **Needs a current last price.** The invalidation check and the STOP check at activation read the
  last price, never the mark price. Without a current one the request answers **503 MSG43**. Until
  TP-0 the cache had no Futures last price, so every Futures plan with an invalidation price, and
  every Futures STOP activation, answered 503 MSG43; **from TP-0 on they are checked against the
  Futures last price** (the close of the latest 1-minute candle) and answer 503 only when it is not
  current. A plan with neither needs no current price to be saved.
- **`maxEntryDeviationR`**: the plan's own limit on a worse MARKET entry, in R; only stricter than
  the system's 0.75. Stored and returned; it is enforced at MARKET activation from TP-C on.
- **`analysisTimeframe`**: defaults from the Trader's trading style (SCALPING `15m`, DAY `1h`,
  SWING and POSITION `4h`, none `1h`); the Trader may pick any of the four. It is the plan's chart
  timeframe (and the timeframe of the indicators stored at the fill); it does **not** choose the
  timeframe of the setup score.
- **`setupScoreAtPlan` / `setupScorePreset`**: taken at activation (Activate and Save and Activate)
  under the preset the Trader's style selects at that moment (a style change after the draft save
  counts), from the latest **closed** candle of **that preset's own timeframe** (SCALPING `15m`,
  DAY_TRADING `1h`, SWING `4h`), whatever `analysisTimeframe` is. It is the number the Setup Score
  card of `GET /analysis` shows at that moment (its `setupScore` is also read on the preset's
  timeframe, whatever `tf` is open), so the plan screen can show the two side by side without a
  mismatch (Q-77, answered again 2026-10-23). A null score never refuses the activation. The score
  is null when that candle is not analysed yet
  (also after an indicator outage: an older candle never stands in) or a component is missing;
  `setupScorePreset` is also null when the score could not be read at all. An activation right
  after a candle closes usually gets a null score: the indicator job writes the new candle's row a
  few seconds after the close, and until then that candle is not analysed. **A null score is not an
  error**: the activation succeeded, the score is not filled in later, show "—"; never compute it on
  the client.
- **INVALIDATED**: a terminal status, listed in the `CANCELLED_EXPIRED` tab with its badge and
  `invalidationReason`. It frees an `ACTIVE_PLAN_MAX` slot. Nothing sets it until TP-B.

---

### POST /plans/calculate
Status: IMPLEMENTED (develop)
Auth: trader (Futures: `FUTURES_ANALYSIS`)
Purpose: Compute the risk panel for the values entered; nothing is saved (SCR-17).

Request: `CreateTradingPlanRequest` (`activate` ignored).

```json
{
  "pairId": "0199a0f0-1111-7aaa-8bbb-000000000001",
  "market": "SPOT",
  "direction": "LONG",
  "entryType": "LIMIT",
  "entryPrice": "62000",
  "stopLoss": "60000",
  "takeProfit": "66000",
  "capital": "1000",
  "riskPercent": "1"
}
```

Response `200`:

```json
{
  "entryPrice": "62000.00",
  "expectedFillPrice": null,
  "capital": "1000",
  "riskPercent": "1",
  "snapshot": {
    "positionQuantity": "0.00500",
    "notionalValue": "310.0000000",
    "initialMargin": "310.00000000",
    "maintenanceMarginRateUsed": null,
    "riskAmount": "10.00000000",
    "rewardAmount": "20.00000000",
    "riskRewardRatio": "2.00000000",
    "estimatedLiquidationPrice": null,
    "estimatedEntryFee": "0.31000000",
    "estimatedStopLossExitFee": "0.30000000",
    "estimatedTakeProfitExitFee": "0.33000000",
    "estimatedSlippage": "0.00000000",
    "lossAtStopLoss": "10.61000000",
    "feeShareOfRisk": "0.06100000",
    "netRiskReward": "1.82469369"
  },
  "warnings": [],
  "blocksActivation": false
}
```

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/15/16 | Input and calculation rules, and the save's validity checks (a MARKET plan with an `invalidationPrice` is MSG01 on that field, as on create) | Under fields / in panel |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | FUTURES on FREE | MSG29 dialog |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Pair not enabled on that market | Inline |
| 503 | `MARKET_PRICE_UNAVAILABLE` | MSG43 | MARKET entry and no live last price; an `invalidationPrice` and no live last price (on Futures: the close of the latest 1-minute candle, from TP-0) | "Price unavailable", retry |

FE notes: SRS asks for panel updates within 300 ms (SCR-17). Debounce input ~200 ms, cancel the
previous request (`AbortController`), keep the last good panel visible while a request is in flight,
show 400 field errors without clearing the panel. Show `warnings` with severity (MSG17) and disable
"Save and Activate" when `blocksActivation`. Decimal scales in the response vary; format for display
(CR-02).
Source: `trading/controller/TradingPlanController.java#L63`; `trading/dto/request/CreateTradingPlanRequest.java#L36`; `trading/dto/response/PlanCalculationResponse.java#L19`; `trading/dto/response/PlanSnapshotResponse.java#L20`. Spec: SRS 3.5.1, BR-21…BR-31, D-69…D-71.

---

### POST /plans
Status: IMPLEMENTED (develop)
Auth: trader (Futures: `FUTURES_ANALYSIS`)
Purpose: Save a plan as DRAFT, or save and activate it (UC-16).

Request: `CreateTradingPlanRequest`; `activate: true` for "Save and Activate".

Response `201`: `TradingPlanResponse` (`status` `DRAFT`, or `ACTIVE` when activated).

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/15/16 | As calculate | Fields |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | FUTURES on FREE | Dialog |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Pair not enabled | Inline |
| 409 | `TRADING_BLOCKING_WARNING` | MSG18 | `activate: true` with a BLOCKING warning; **nothing is saved** | Banner; offer "Save as Draft" |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | `activate: true` and `ACTIVE_PLAN_MAX` reached (FREE: 3); nothing saved | Inline + upgrade |
| 503 | `MARKET_PRICE_UNAVAILABLE` | MSG43 | MARKET, no live last price; `invalidationPrice`, or STOP with `activate: true`, and no live last price (Futures last price from TP-0) | Retry |

FE notes: show MSG14 (draft) or MSG19 (activated). Warnings are stored with the plan and replaced on
each save. A DRAFT with warnings is allowed.
Source: `trading/controller/TradingPlanController.java#L79`; `trading/dto/response/TradingPlanResponse.java#L39`. Spec: SRS 3.5.1, UC-16, BR-31, BR-62, D-63, D-72.

---

### GET /plans
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: The caller's plans, newest first (SCR-16, UC-20).

| Query | Type | Required | Rule |
|---|---|---|---|
| `tab` | `DRAFT` \| `ACTIVE` \| `EXECUTED` \| `CANCELLED_EXPIRED` | no | all statuses when absent; upper case; `CANCELLED_EXPIRED` also lists INVALIDATED (TP-A) |
| `pairId` | UUID | no | |
| `market` | `SPOT` \| `FUTURES` | no | **upper case only** here (unlike `/market`) |
| `from` | ISO instant | no | created at or after |
| `to` | ISO instant | no | created before |
| `page` | int | no | ≥ 1 → MSG15 `errors.page` |
| `pageSize` | int | no | 1–100, default 20 → MSG15 `errors.pageSize` |

Response `200`: `PageResponse<TradingPlanSummary>`.

```json
{
  "items": [
    {
      "id": "0199a2c4-0000-7000-8000-000000000001",
      "pairId": "0199a0f0-1111-7aaa-8bbb-000000000001",
      "market": "SPOT", "direction": "LONG", "entryType": "LIMIT",
      "entryPrice": "62000.00", "stopLoss": "60000.00", "takeProfit": "66000.00",
      "leverage": null, "riskAmount": "10.00000000", "riskRewardRatio": "2.00000000",
      "status": "DRAFT",
      "createdAt": "2026-10-03T02:20:00Z", "activatedAt": null, "expiresAt": "2026-10-10T02:20:00Z"
    }
  ],
  "page": 1, "pageSize": 20, "total": 1
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/MSG15 | Bad enum, UUID, instant, paging |

FE notes: no symbol in rows — resolve `pairId` from data you already hold (FEQ-01). Position status
and P/L of executed plans (SRS 3.5.2) are not in the row yet (T-042+). Keep the tab in the URL.
Source: `trading/controller/TradingPlanController.java#L90`; `trading/dto/response/TradingPlanSummaryResponse.java#L32`. Spec: SRS 3.5.2, UC-20, CR-04, D-73.

---

### GET /plans/{id}
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: One plan with snapshot, warnings and status history (SCR-18).

Response `200`: `TradingPlanResponse`.

```json
{
  "id": "0199a2c4-0000-7000-8000-000000000001",
  "pairId": "0199a0f0-1111-7aaa-8bbb-000000000001",
  "market": "SPOT", "direction": "LONG", "entryType": "LIMIT",
  "entryPrice": "62000.00", "stopLoss": "60000.00", "takeProfit": "66000.00",
  "capital": "1000", "riskPercent": "1",
  "leverage": null, "marginMode": null,
  "expiresAt": "2026-10-10T02:20:00Z", "note": null,
  "status": "DRAFT", "editable": true,
  "snapshot": {
    "positionQuantity": "0.00500", "notionalValue": "310.0000000", "initialMargin": "310.00000000",
    "maintenanceMarginRateUsed": null, "riskAmount": "10.00000000", "rewardAmount": "20.00000000",
    "riskRewardRatio": "2.00000000", "estimatedLiquidationPrice": null
  },
  "warnings": [],
  "blocksActivation": false,
  "statusHistory": [ { "status": "DRAFT", "at": "2026-10-03T02:20:00Z" } ]
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Unknown id or another user's plan (never 403) |

FE notes: show Edit only when `editable`. Activate for DRAFT; Cancel for DRAFT and ACTIVE. The live
position block (SRS 3.5.3) waits for T-042+ (and the planned `/user/queue/positions`).
Source: `trading/controller/TradingPlanController.java#L109`; `trading/dto/response/StatusChangeResponse.java#L14`; `trading/dto/response/PlanWarningResponse.java#L15`. Spec: SRS 3.5.3, D-67.

---

### PUT /plans/{id}
Status: IMPLEMENTED (develop)
Auth: trader (Futures: `FUTURES_ANALYSIS`)
Purpose: Edit a DRAFT, optionally activate it (UC-17).

Request: `UpdateTradingPlanRequest` (no `pairId`). Full replacement of the inputs.

Response `200`: `TradingPlanResponse`.

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/15/16 | As calculate | Fields |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | FUTURES on FREE | Dialog |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's plan, or pair no longer enabled | Inline |
| 409 | `TRADING_PLAN_STATUS_TRANSITION_INVALID` | MSG43 | Plan is not DRAFT | Reload plan |
| 409 | `TRADING_BLOCKING_WARNING` | MSG18 | `activate: true` with a BLOCKING warning | Banner |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | `activate: true` at the limit | Inline |
| 409 | `DATA_CONFLICT` | MSG43 | Changed concurrently | Reload |
| 503 | `MARKET_PRICE_UNAVAILABLE` | MSG43 | MARKET, no live last price; `invalidationPrice`, or STOP with `activate: true`, and no live last price (Futures last price from TP-0) | Retry |

Source: `trading/controller/TradingPlanController.java#L124`; `trading/dto/request/UpdateTradingPlanRequest.java#L33`. Spec: SRS 3.5.1, UC-17, BR-32.

---

### POST /plans/{id}/activate
Status: IMPLEMENTED (develop)
Auth: trader (Futures: `FUTURES_ANALYSIS`)
Purpose: DRAFT → ACTIVE after re-checking with the current price and the plan limit (UC-18).

Request: no body.

Response `200`: `TradingPlanResponse` (`status: "ACTIVE"`, new snapshot).

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/15/16 | Inputs no longer pass (e.g. MARKET price moved past the stop → `errors.stopLoss` MSG16); a STOP already triggered → `errors.entryPrice` MSG16; the invalidation price now on the wrong side → `errors.invalidationPrice` MSG16; expiry already passed → MSG01 | Fields / banner; offer Edit |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | Futures plan, plan downgraded | Dialog |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's, or pair disabled | Inline |
| 409 | `TRADING_PLAN_STATUS_TRANSITION_INVALID` | MSG43 | Not DRAFT (double click, other tab) | Reload |
| 409 | `TRADING_BLOCKING_WARNING` | MSG18 | BLOCKING warning after re-check | Banner |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | `ACTIVE_PLAN_MAX` | Inline + upgrade |
| 503 | `MARKET_PRICE_UNAVAILABLE` | MSG43 | MARKET, no live last price; STOP or `invalidationPrice` and no live last price (Futures last price from TP-0) | Retry |

FE notes: show MSG19 on success. The response carries `setupScoreAtPlan` (may be null) and
`setupScorePreset` taken at this activation. Disable the button while in flight. The snapshot can differ from the
draft's (MARKET entry = price at activation; other open risk recounted).
Source: `trading/controller/TradingPlanController.java#L142`. Spec: SRS 3.5.3, UC-18, BR-31, BR-62, D-63, D-72.

---

### POST /plans/{id}/cancel
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: DRAFT or ACTIVE → CANCELLED (UC-19).

Request: no body. Confirm with MSG20 first.

Response `200`: `TradingPlanResponse` (`status: "CANCELLED"`).

| Status | `code` | MSG | When |
|---|---|---|---|
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's |
| 409 | `TRADING_PLAN_STATUS_TRANSITION_INVALID` | MSG43 | EXECUTED, CANCELLED, EXPIRED or INVALIDATED |
| 409 | `DATA_CONFLICT` | MSG43 | Changed concurrently (e.g. a fill, later) |

Source: `trading/controller/TradingPlanController.java#L154`. Spec: SRS 3.5.3, UC-19.

---

### POST /plans/{id}/close-position
Status: PLANNED (spec only)
Auth: trader
Purpose: Close an open simulated position at the current last price (UC-21, SCR-19, MSG21).

No code. Depends on the matching engine (T-042…T-046). Shape unknown; TD 8 lists only the path.
Source: none. Spec: TD 8, SRS 3.5.3, UC-21, BR-39.
