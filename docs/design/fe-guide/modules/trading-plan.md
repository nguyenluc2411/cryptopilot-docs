# Module: trading (trading plans)

Screens SCR-16 (plan list), SCR-17 (create/edit with live risk panel), SCR-18 (plan detail),
SCR-19 (close position, planned). All endpoints: TRADER only.
Code prefix: `backend/src/main/java/com/cryptopilot/trading/`. Controller: `controller/TradingPlanController.java`.

Read first:

- **Futures plans cannot be sized in any environment today.** No leverage brackets are stored (they
  need the admin screen, T-085), so every `market: "FUTURES"` calculate/create/activate answers 400
  `errors.leverage` MSG15 (D-70). FREE users get 403 MSG29 first.
- **Plans fill.** A MARKET plan, and a LIMIT the price already reached, fill at activation; the
  engine fills a resting LIMIT and triggers a STOP (TP-B) later. A filled plan is `EXECUTED` and,
  with T-048a, carries a `position` block (below). Still missing: `EXPIRED` (no expiry job yet,
  so an ACTIVE plan past `expiresAt` stays ACTIVE) and closing a position (SCR-19, T-048b).
- Plan responses carry `pairId` but **no symbol** (FEQ-01).
- **Breaking (TP-D, D-121), branch `feat/tp-d-account-capital`, not on `develop` yet: no `capital`
  in the requests.** Every plan is sized on the Trader's account size, the profile's
  `defaultCapital` (SCR-07). SCR-17 shows the capital **read-only** with a link to SCR-07; it is no
  longer an input. See "Account capital (TP-D)" below.
- **Position of a filled plan (T-048a), branch `feat/t-048a-journal-open`, not on `develop` yet:**
  `GET /plans/{id}` (and the create / update / activate responses) carry a `position` block once the
  plan is `EXECUTED`, and list rows carry `positionStatus`. See "Position of an executed plan
  (T-048a)" below.
- **Exits (T-048b), branch `feat/t-048b-journal-exits`, not on `develop` yet:** the engine closes a
  position by its take profit, stop loss or liquidation; the `position` block then carries the exit,
  realized, fees, funding, net and `provisional`, and the change is pushed on `/user/queue/positions`.
  See "Exits of a position (T-048b)" below.
- **Plan validity (TP-A, D-111, D-112), branch `feature/TP-A-plan-validity`, not on `develop` yet:**
  STOP entry, invalidation price, own entry deviation limit, analysis timeframe, the INVALIDATED status
  and the setup score taken at activation. See "Plan validity (TP-A)" below.
- **STOP trigger and invalidation (TP-B), branch `feat/tp-b-stop-invalidation`, stacked on TP-0, not
  on `develop` yet:** the engine triggers STOP entries and invalidates waiting plans, so **STOP can
  be offered in the web (T-040)** once TP-B is on `develop`. See "Engine: STOP trigger and
  invalidation (TP-B)" below.
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
  riskPercent?: string | null;        // default: profile defaultRiskPercent, else risk profile's risk per trade
  leverage?: number | null;           // default 1; SPOT must be 1 or absent
  expiresAt?: string | null;          // LIMIT and STOP default now + 7 days
  note?: string | null;
  invalidationPrice?: string | null;  // TP-A; LIMIT and STOP only; see "Plan validity"
  maxEntryDeviationR?: string | null; // TP-A; > 0 and <= ENTRY_DEVIATION_BLOCK_R (0.75)
  analysisTimeframe?: '15m' | '1h' | '4h' | '1d' | null;  // TP-A; default from the trading style
  activate?: boolean | null;          // true = "Save and Activate"
  confirmDeviation?: boolean | null;  // TP-C; true = the Trader confirmed MSG51; read only with activate: true
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
  capital: string;                    // TP-D: always the profile's defaultCapital; show read-only
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
  capital: string;                    // TP-D: profile defaultCapital at the last save, or at activation
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
| `capital` | TP-D: not a request field (ignored if sent). The profile has no `defaultCapital` (or one ≤ 0) → MSG01 `errors.capital` on calculate, create, update and activate: link the Trader to SCR-07 |
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

## Account capital (TP-D)

D-121, branch `feat/tp-d-account-capital`, not on `develop` yet. **Breaking for SCR-17.**

- The capital of a plan is the Trader's account size: the `defaultCapital` of the profile
  (`GET /me/profile`, set on SCR-07). Every plan of the Trader uses that one number.
- `POST /plans/calculate`, `POST /plans` and `PUT /plans/{id}` **no longer accept `capital`**. A body
  that still sends it is not refused; the value is ignored and the profile's capital is used.
- The responses keep `capital` (calculation and plan detail), so the panel can show the figure.
- **SCR-17:** make the capital field read-only, showing the profile value (or `capital` from the
  last `/plans/calculate`), with a link "Change in Profile & Settings" to SCR-07. `riskPercent`
  stays an input per plan, pre-filled from the profile as before.
- **No default capital** (never set, cleared, or ≤ 0): calculate, create, update and activate answer
  400 with `errors.capital` = MSG01. Show it on the capital field with the SCR-07 link.
- **Snapshot:** each save stores the profile capital of that moment; activation recalculates the plan
  on the profile capital of the activation (BR-31), so `capital`, `positionQuantity`, `riskAmount`
  and the warnings of an ACTIVE plan may differ from its draft. A later profile change never
  changes a stored plan.
- **TOTAL_OPEN_RISK** divides the risk of all ACTIVE plans and open positions by the **current**
  profile capital. INSUFFICIENT_CAPITAL (BR-25 Spot notional, BR-26 Futures margin) compares with
  the plan's capital, checked again at activation.
- After the Trader changes `defaultCapital` on SCR-07, recalculate an open SCR-17 panel.

## Plan validity (TP-A)

Status: on `feature/TP-A-plan-validity` (not merged). Spec: BR-33, BR-68, BR-69, BR-70; D-111, D-112.

- **STOP entry.** A stop-market entry for breakouts: `entryPrice` is the stop price. LONG triggers
  when the last price is ≥ the stop, SHORT when ≤. Without an expiry it gets 7 days, as LIMIT.
  Activating (Activate or Save and Activate) a STOP the last price has already reached answers 400
  `errors.entryPrice` MSG16; it is never turned into MARKET — offer MARKET to the Trader. How an
  ACTIVE STOP triggers and fills: "Engine: STOP trigger and invalidation (TP-B)". Offer STOP in the
  entry type selector once TP-B is on `develop`; before that it is accepted but never triggers.
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
  the system's 0.75. Stored and returned; enforced at MARKET activation, see "Entry deviation at
  MARKET activation (TP-C)".
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
  `invalidationReason`. It frees an `ACTIVE_PLAN_MAX` slot. The matching engine sets it (TP-B).

## Engine: STOP trigger and invalidation (TP-B)

Status: on `feat/tp-b-stop-invalidation` (stacked on TP-0, not merged). Spec: BR-33, BR-36, BR-68,
NSF-07; D-77, D-78, D-111, D-112. Nothing in the request or response shapes changes; plans move to
`EXECUTED` or `INVALIDATED` on their own, so refetch (or poll) the plan list and detail.

- **STOP trigger.** An ACTIVE STOP waits for the Futures or Spot **last** price (never the mark
  price): LONG triggers when a price ≥ the stop trades, SHORT when ≤. Equal to the stop counts.
- **STOP fill price.** It is a stop-market order: it fills at the stop price, or at the **open of
  the 1-minute candle** when that candle already opened past the stop (a gap: a LONG stop 100 and a
  candle opening at 101 fills at 101). The price is then moved by `SLIPPAGE_BPS` against the Trader
  and rounded to the tick; nothing caps it. It always pays the **taker** fee. A STOP fill can
  therefore be worse than the stop price; say so in the STOP help text ("fills at the stop or
  worse on a gap").
- **LIMIT fill price** (unchanged): a resting LIMIT reached by the price fills at its own price, also
  through a gap, as **maker**, with no slippage.
- **Fill time.** `executedAt` (and `invalidatedAt`) is the open time of the candle that decided it,
  not the moment the server noticed; after a server restart the missed candles are replayed with the
  same rules and give the same result.
- **Invalidation.** A waiting plan becomes `INVALIDATED` before its entry fills when the price
  reaches first: a LIMIT's take profit (`TAKE_PROFIT_REACHED`), a STOP's stop loss
  (`STOP_LOSS_REACHED`), or the plan's `invalidationPrice` (`INVALIDATION_PRICE`). When one candle
  reaches both the entry and an invalidation level, the candle's open decides if it already lies
  past one of them; otherwise invalidation wins. A candle that opened before the activation neither
  fills nor invalidates the plan.
- **Activation refusals.** Activate and Save and Activate also answer 400 MSG16 on
  `errors.takeProfit` for a LIMIT whose take profit the last price has already reached, and on
  `errors.stopLoss` for a STOP whose stop loss it has already reached (at the level counts), so no
  plan becomes ACTIVE only to be invalidated at once. Fill `{rule}` of MSG16 yourself (M-11), e.g.
  "take profit must be above the current price".
- **Races.** A cancel and the engine's fill or invalidation never both happen: the loser of a cancel
  gets 409 MSG43; reload the plan to show its new status.
- **Notification.** The Trader's notice of an invalidation (MSG54, with the reason) is T-046; until
  then the web learns it only from the plan's status.

## Position of an executed plan (T-048a)

Branch `feat/t-048a-journal-open`, not on `develop` yet. When a plan fills (the engine fills a
resting LIMIT or triggers a STOP, or a LIMIT / MARKET fills at activation) the journal records its
position in the same transaction, and the plan responses expose it. A plan that was `EXECUTED`
before T-048a has no position: `position` and `positionStatus` are `null` (D-118 note; local
databases are reset, nothing is backfilled).

`TradingPlanResponse.position` — `null` until the plan is `EXECUTED`:

```ts
interface PositionResponse {
  status: 'OPEN' | 'CLOSED';
  fillPrice: string;          // actual fill price of the entry (slippage included)
  quantity: string;           // the snapshot's positionQuantity
  entryTime: string;          // ISO instant: the 1-minute candle open of an engine fill, else the activation instant
  entryFee: string;           // fee paid on the entry, by liquidity role (maker / taker)
  liquidationPrice: string | null;  // Futures: at the fill price (T-048b; was the snapshot's estimate); null on Spot
  currentPrice: string | null;      // OPEN only: Futures mark price, Spot last price; null when CLOSED or not cached
  unrealizedPnl: string | null;     // OPEN only: (currentPrice − fillPrice) × quantity, LONG; mirrored for SHORT
  // T-048b, CLOSED only (null while OPEN):
  exitPrice: string | null;         // exit fill: TP at its price, SL after slippage, liquidation at liquidationPrice
  exitTime: string | null;          // ISO instant: open of the 1-minute candle (last or mark price) that decided it
  closeReason: 'TAKE_PROFIT' | 'STOP_LOSS' | 'LIQUIDATION' | null;   // MANUAL comes with T-046
  realizedPnl: string | null;       // price result only, no fees, no funding (BR-35)
  feeAmount: string | null;         // entry fee + exit fee; a liquidation: entry fee + clearance fee (BR-36)
  fundingFeeAmount: string | null;  // Futures: signed funding known so far, + received / − paid; null on Spot
  netPnl: string | null;            // realizedPnl − feeAmount + fundingFeeAmount (BR-38)
  provisional: boolean;             // true: a funding settlement is still missing, netPnl may change; false while OPEN
}
```

```json
"position": {
  "status": "OPEN", "fillPrice": "100.000000000000", "quantity": "2.000000000000",
  "entryTime": "2026-10-25T08:00:00Z", "entryFee": "0.20000000",
  "liquidationPrice": null, "currentPrice": "103", "unrealizedPnl": "6.00000000"
}
```

- The live P/L of SCR-18 is `unrealizedPnl`: unrealized by mark price, **no fees, no funding**
  (Q-55). Show it with the label "unrealized"; the entry fee is shown on its own.
- `currentPrice` / `unrealizedPnl` are `null` when the price cache holds no current price (show a
  dash, not 0) and always `null` once `CLOSED`.
- `TradingPlanSummaryResponse.positionStatus`: `OPEN` / `CLOSED` on `EXECUTED` rows, else `null`.
- An open position keeps its `ACTIVE_PLAN_MAX` slot (BR-62): the MSG27 banner counts ACTIVE plans
  plus open positions. The TOTAL_OPEN_RISK warning (BR-29) also adds the risk of open positions.
- Close-position and the journal screens come later (T-046, T-049).

Source: `trading/dto/response/PositionResponse.java`; `trading/service/impl/TradingPlanServiceImpl.java`
(`detail`, `list`). Spec: BR-34, BR-62, BR-29, UC-20, SCR-16, SCR-18, Q-55, D-119.

## Exits of a position (T-048b)

Branch `feat/t-048b-journal-exits`, not on `develop` yet. The engine closes an OPEN position on its
own; the Trader does nothing. The plan stays `EXECUTED`; its `position.status` becomes `CLOSED`.

| Exit | Price source | Fills at | Fee |
|---|---|---|---|
| Take profit | last price (1-minute candles) | the take profit, also when the candle opened beyond it | maker |
| Stop loss | last price | the stop, or the candle open when it opened beyond it, then moved by `SLIPPAGE_BPS` against the Trader | taker |
| Liquidation (Futures) | **mark** price | `liquidationPrice`, always | clearance fee instead of the taker fee |

- **New activation refusal:** a plan whose stop loss the current last price has already reached
  (LONG last ≤ SL, SHORT last ≥ SL) is refused with 400 MSG16 on `stopLoss`, for LIMIT, STOP and
  MARKET, on Activate and on Save and Activate. Futures checks the last price, never the mark. Show it
  on the stop loss field.
- One candle reaching both levels: the level its open is already at or beyond decides; otherwise the
  stop loss wins (Q-61, BR-35).
- The candle in which the entry filled can only stop the position out, never take profit (the order
  inside the minute is unknown). A LIMIT that filled at activation already beyond its stop loss exits
  at once at its entry price.
- A CLOSED example (T-044 case (c), a liquidation):

```json
"position": {
  "status": "CLOSED", "fillPrice": "100.000000000000", "quantity": "2.000000000000",
  "entryTime": "2026-10-25T08:01:00Z", "entryFee": "0.04000000", "liquidationPrice": "90.370000000000",
  "currentPrice": null, "unrealizedPnl": null,
  "exitPrice": "90.370000000000", "exitTime": "2026-10-25T08:02:00Z", "closeReason": "LIQUIDATION",
  "realizedPnl": "-19.26000000", "feeAmount": "0.76296000", "fundingFeeAmount": "0.00000000",
  "netPnl": "-20.02296000", "provisional": false
}
```

- Show realized, fees, funding and net separately (D-97). **Net is the P/L to headline**; it is the
  `{pnl}` of MSG23 / MSG24.
- `provisional: true` means a funding settlement of the position was not stored yet when it closed.
  Show the net with a "provisional" tag; the backend recomputes it once the settlement arrives (every
  10 minutes) and the next read shows the final value. A close is never delayed by this.
- A closed position frees its `ACTIVE_PLAN_MAX` slot (MSG27) and leaves the TOTAL_OPEN_RISK warning.
- The Trader gets a notification: MSG23 "{pair} position closed by take profit|stop loss at {price}.
  P/L: {net}." or MSG24 "{pair} position was liquidated at {price}. Loss: {net}." (`type` PLAN,
  `referenceType` PLAN, `referenceId` = the plan id).
- Push: `/user/queue/positions` sends a `PositionUpdate` when a position closes (see
  `05-realtime.md`); re-read `GET /plans/{id}` for the full block.

Source: `trading/matching/ExitRule.java`, `trading/service/impl/PositionCloser.java`,
`trading/job/PositionUserFeed.java`, `trading/dto/response/PositionUpdateResponse.java`. Spec: BR-35,
BR-36, BR-37, BR-38, UC-20, SCR-18, MSG23, MSG24, D-97, Q-56, Q-57, Q-59, Q-61.

## Manual close of a position (T-046)

Branch `feat/t-046-manual-close`, stacked on T-048b (PR #75), not on `develop` yet. Contract fixed by
the team lead on 2026-10-25; build SCR-19 (Close Position pop-up, MSG21) on it. Spec: UC-21, BR-39,
BR-36, BR-38, MSG21, MSG23.

**1. Estimate** — `GET /api/v1/plans/{id}/close-estimate` → 200:

```ts
interface CloseEstimate {
  currentPrice: string;        // current last price (Futures: the last price, never the mark price)
  estimatedExitPrice: string;  // currentPrice moved by SLIPPAGE_BPS against the Trader (a taker sell for LONG, buy for SHORT), on the tick
  priceResult: string;         // (estimatedExitPrice − fillPrice) × quantity for LONG, mirrored for SHORT
  entryFee: string;            // the entry fee stored at the fill
  estimatedExitFee: string;    // estimatedExitPrice × quantity × taker rate of the market
  fundingSoFar: string | null; // Futures: signed funding settled since the fill, + received / − paid; null on Spot
  fundingProvisional: boolean; // true: a settlement may still be missing from fundingSoFar; false on Spot
  estimatedNetPnl: string;     // priceResult − entryFee − estimatedExitFee + (fundingSoFar ?? 0)
  at: string;                  // ISO instant the estimate was computed
}
```

- MSG21 "Close this position at about {price}? Estimated P/L: {pnl}." uses `estimatedExitPrice` and
  `estimatedNetPnl`. The estimate is not stored and does not reserve the price: the close executes at
  the price of its own moment.

**2. Close** — `POST /api/v1/plans/{id}/close-position` (no body) → 200 `TradingPlanResponse` whose
`position` is `CLOSED` with `closeReason: "MANUAL"`. The close is a taker sell (LONG) or buy (SHORT) at
the current last price moved by `SLIPPAGE_BPS`; exit fee at the taker rate; funding up to the close;
net P/L as for every exit (BR-38). The Trader also gets MSG23 (`{reason}` "manual close") and a
`PositionUpdate` on `/user/queue/positions`.

**Errors (both endpoints)**

| Status | `messageCode` | When |
|---|---|---|
| 404 | — (`NOT_FOUND`) | the plan is not the caller's |
| 409 | MSG43 | the plan has no OPEN position (not executed yet, or already closed, e.g. by the engine first) |
| 503 | MSG43 | no current last price is cached for the pair |

**Field names of the CLOSED position block** are those of T-048b ("Exits of a position" above):
`exitPrice`, `exitTime`, `closeReason`, `realizedPnl`, `feeAmount`, `fundingFeeAmount`, `netPnl` and the
boolean **`provisional`** (there is no `fundingIncomplete` field in the response: `provisional` is that
flag, true while a funding settlement is missing).

Source: `trading/controller/TradingPlanController.java`, `trading/dto/response/CloseEstimateResponse.java`.

## Edit the stop loss and take profit of an open position (TP-E)

Branch `feat/tp-e-edit-open-levels`, not on `develop` yet. Decision D-124 (team lead, 2026-10-23):
a Trader may move the stop loss and the take profit of an OPEN position. Partial closing stays out
(D-11). Build "Edit SL/TP" on SCR-18 on this contract. Spec: UC-21, BR-22, BR-28, BR-29, BR-42, D-124.

**Request** — `PATCH /api/v1/plans/{id}/position-levels` (`id` = the plan id, as for close-position):

```ts
interface ChangePositionLevelsRequest {
  stopLoss?: string | null;    // new stop loss; absent or null keeps the current one
  takeProfit?: string | null;  // new take profit; absent or null keeps the current one
}
```

- At least one of the two → otherwise 400 MSG01 on `stopLoss`.
- Each value > 0, ≤ 16 integer / 12 decimal digits → MSG15; rounded to the pair's tick (half-up)
  before every check, as on plan entry.
- Checked against the **current last price** (Futures: the last price, never the mark price), MSG16
  on the field:
  - LONG: `stopLoss < lastPrice < takeProfit`; SHORT: `takeProfit < lastPrice < stopLoss`;
  - a level the last price has already reached is refused, never executed at once;
  - Futures: the stop loss must stay before `position.liquidationPrice` (LONG above it, SHORT below
    it). This one is blocking, as on plan entry (BR-28).
- Only the fields sent are checked; a value equal to the current level changes nothing.

**Response** — 200 `TradingPlanResponse`, with `position` updated. New fields of `PositionResponse`
(on every read of the plan, OPEN and CLOSED):

```ts
interface PositionResponse {
  // ... T-048a / T-048b / T-046 fields unchanged ...
  stopLoss: string | null;            // the CURRENT stop loss (the exits use this one)
  takeProfit: string | null;          // the CURRENT take profit
  originalStopLoss: string | null;    // the levels at the fill; never change (= the plan's stopLoss / takeProfit)
  originalTakeProfit: string | null;
  stopWidened: boolean;               // true once a stop loss was moved further from the entry than the original
  levelChangeCount: number;           // how many changes were made
  levelChanges: LevelChange[];        // every change, oldest first; [] when none
  breakevenPrice: string | null;      // OPEN only, see "Move SL to breakeven"; null when CLOSED
  breakevenProvisional: boolean;      // true: a funding settlement may be missing from it (Futures)
  levelWarnings: PlanWarningResponse[];  // only in the PATCH response, see "Warnings"; [] on every other read
}

interface LevelChange {
  changedAt: string;                  // ISO instant of the change
  oldStopLoss: string | null;  oldTakeProfit: string | null;
  newStopLoss: string | null;  newTakeProfit: string | null;
}
```

**When a new level acts.** The exits use the new levels from the next 1-minute candle (a candle that
opened at or after `changedAt`); the rest of the minute in which the change was made is still decided
by the previous levels, so a replay after downtime gives the same exit as live processing (the same
rule as a plan activated in the middle of a minute). Say so in the edit dialog ("applies from the next
minute"). Exit pricing does not change: a stop loss exits as a taker with slippage, a take profit at
its own price as a maker.

**Result in R.** The realized R of the journal keeps the ORIGINAL planned risk (BR-42): moving a stop
does not change the risk the trade is measured against, so a widened stop that is then hit shows a loss
larger than −1R. Show `stopWidened` on SCR-18 and in the journal ("stop moved away"), and the history
from `levelChanges`; the AI review uses the same data.

**Move SL to breakeven.** A stop loss at the entry price still loses the fees. `breakevenPrice` is the
stop price at which the net P/L is zero: the entry fee paid, the taker exit fee and the slippage of the
stop, and on Futures the funding so far. It is on the tick and rounded against the Trader (LONG up,
SHORT down). The shortcut button sends `{ "stopLoss": breakevenPrice }`, **never the bare entry
price**; tooltip: "Moves the stop to the price that covers the entry fee, the exit fee and slippage
(and funding so far), so a stop-out ends at about zero net P/L." Tag it "provisional" when
`breakevenProvisional` is true. The button can only succeed once the last price is beyond
`breakevenPrice` (LONG above, SHORT below); otherwise the request answers MSG16 on `stopLoss`, so
disable it until then.

**Warnings** (`position.levelWarnings`, non-blocking, shown like MSG17): when the change widens the
stop loss (further from the entry than the current one) and the new risk breaks a limit of the risk
profile:

| `type` | When |
|---|---|
| `OVERSIZED_POSITION` | the position's risk at the new stop / profile capital > the profile's risk per trade |
| `TOTAL_OPEN_RISK` | the open risk with the new stop / profile capital > the profile's maximum total open risk |

The change is saved anyway (whether it should be refused is an open question for the team lead).

**Open risk.** TOTAL_OPEN_RISK (the risk panel warning, BR-29) now counts an open position at its
CURRENT risk: quantity × |entry − current stop loss| when the stop is on the losing side, 0 once the
stop is at or past the entry. Moving a stop to breakeven frees the risk budget for new plans.

**Errors**

| Status | `messageCode` | When |
|---|---|---|
| 400 | MSG01 | neither `stopLoss` nor `takeProfit` sent (`errors.stopLoss`) |
| 400 | MSG15 | a value ≤ 0 or with too many digits (`errors.<field>`) |
| 400 | MSG16 | wrong side of the current last price, already reached, or (Futures) the stop loss at or past `liquidationPrice` (`errors.<field>`) |
| 401 | MSG44 | no valid session |
| 404 | — (`NOT_FOUND`) | the plan is not the caller's |
| 409 | MSG43 | the plan has no OPEN position: not executed, already closed, or closed (by TP, SL, liquidation or a manual close) while the change was being made; nothing changed |
| 503 | MSG43 | no current last price is cached for the pair |

Source: `trading/controller/PositionLevelController.java`,
`trading/service/impl/PositionLevelServiceImpl.java`, `trading/calculator/BreakevenCalculator.java`.

## Entry deviation at MARKET activation (TP-C)

Status: on `feat/tp-c-entry-deviation` (stacked on TP-B, not merged). Spec: BR-69, MSG51, MSG52;
D-111 M2, D-112 R7. For T-113 (the confirmation dialog).

- **Only MARKET plans**, on Activate and on Save and Activate (`POST /plans`, `PUT /plans/{id}` with
  `activate: true`). LIMIT and STOP have no activation check; their deviation is recorded at the fill
  (T-048c).
- **What is measured.** `deviationR = d × (expectedFill − plannedEntry) / |plannedEntry − stopLoss|`,
  d = +1 LONG, −1 SHORT; **positive = a worse entry**, negative = a better one. `plannedEntry` is the
  plan's `plannedEntryPrice`, the unslipped last price of its **last draft save**. `expectedFill` is
  the current last price (Futures: the Futures last price, never the mark) moved by `SLIPPAGE_BPS`
  against the Trader, the `expectedFillPrice` the plan is re-sized on. On **Save and Activate** the
  request is itself the last save, so `plannedEntry` is this request's last price and only the
  slippage can move the entry (0 bps today: Save and Activate is never asked to confirm).
- **Bands** (`ENTRY_DEVIATION_CONFIRM_R` 0.25, limit = `maxEntryDeviationR` when set, else
  `ENTRY_DEVIATION_BLOCK_R` 0.75; both read from the settings on each call):
  - below 0.25, or negative → activated as before;
  - 0.25 up to and including the limit → **400 `ENTRY_DEVIATION_CONFIRMATION_REQUIRED` MSG51**,
    nothing changes; repeat the **same request** with the confirmation;
  - above the limit, or the expected fill **at or past the take profit** → **409
    `ENTRY_DEVIATION_REFUSED` MSG52**, also with the confirmation; the plan stays a DRAFT.
  - A `maxEntryDeviationR` below 0.25 leaves no band to confirm: up to it activates, above it MSG52.
- **Order of refusals.** MSG16 (inputs no longer pass), MSG18 (BLOCKING warning) and MSG27 (plan
  limit) come before MSG51, so the dialog never asks to confirm a plan that would then be refused.
  MSG52 for the take profit replaces the MSG16 on `errors.takeProfit` that a MARKET plan used to get
  there.
- **Retry with the confirmation.**
  - Activate: `POST /plans/{id}/activate?confirmDeviation=true` (query parameter; still no body).
  - Save and Activate: the same body with `"confirmDeviation": true` added.
  - The confirmation accepts whatever deviation the retry finds within the band; if the price moved
    further, the retry can answer MSG52, or proceed with no dialog.
- **MSG51 body** (RFC 9457 problem detail; every value a decimal string, scale as in the plan
  snapshot). `messageArgs` = `[deviation, quantity, rr]` for "The price has moved {deviation}R from
  your plan. New quantity {quantity}, risk/reward {rr}. Activate anyway?". Round for display
  (deviation and R:R to 2 decimals).

  ```json
  {
    "type": "about:blank", "title": "Bad Request", "status": 400,
    "detail": "the MARKET entry moved 0.50000000R from the plan and needs confirmation",
    "code": "ENTRY_DEVIATION_CONFIRMATION_REQUIRED", "messageCode": "MSG51", "traceId": "…",
    "messageArgs": ["0.50000000", "0.033300000000", "1.66666667"],
    "deviationR": "0.50000000",
    "maxDeviationR": "0.75000000",
    "expectedFillPrice": "101000",
    "positionQuantity": "0.033300000000",
    "riskRewardRatio": "1.66666667",
    "netRiskReward": "1.49828071"
  }
  ```

  `netRiskReward` is the R:R after fees of TP-0 (show it as "R:R after fees"). The risk amount does
  not change: the quantity is re-sized so the risk stays the planned one.
- **MSG52 body.** `messageArgs` = `[deviation, max]` for "The price has moved {deviation}R from your
  plan, beyond the allowed {max}R or past the take profit. The plan was not activated."

  ```json
  {
    "status": 409, "code": "ENTRY_DEVIATION_REFUSED", "messageCode": "MSG52",
    "messageArgs": ["1.00000000", "0.75000000"],
    "deviationR": "1.00000000", "maxDeviationR": "0.75000000", "expectedFillPrice": "102000",
    "takeProfitReached": false
  }
  ```

  `takeProfitReached` (boolean) says which half of the sentence applies. Offer Edit (a new draft save
  takes the new price as the planned entry) or Cancel.
- **Example** (BTC LONG MARKET saved at 100,000, SL 98,000, TP 106,000, risk 100 USDT, 0 bps, step
  0.0001): last 100,000 → 0R, activated, quantity 0.05, R:R 3.0; last 101,000 → 0.5R, MSG51 with
  quantity 0.0333, R:R 1.67, then activated with the flag; last 102,000 → 1.0R, MSG52 (it would be
  quantity 0.025, R:R 1.0); last ≥ 106,000 → MSG52 with `takeProfitReached: true`. SHORT mirror: SL
  102,000, TP 94,000, last 99,000 → 0.5R. With `maxEntryDeviationR` 0.5, last 101,200 (0.6R) →
  MSG52. With 10 bps, last 100,400 buys at 100,500.40 → 0.2502R → MSG51 (at 0 bps: 0.2R, activated).

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
  "riskPercent": "1"
}
```

Response `200`:

```json
{
  "entryPrice": "62000.00",
  "expectedFillPrice": null,
  "capital": "1000.00000000",
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
| 400 | `ENTRY_DEVIATION_CONFIRMATION_REQUIRED` | MSG51 | TP-C: MARKET with `activate: true` whose expected fill is 0.25R up to the limit from the plan; nothing saved | Dialog; resend with `"confirmDeviation": true` |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | FUTURES on FREE | Dialog |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Pair not enabled | Inline |
| 409 | `TRADING_BLOCKING_WARNING` | MSG18 | `activate: true` with a BLOCKING warning; **nothing is saved** | Banner; offer "Save as Draft" |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | `activate: true` and `ACTIVE_PLAN_MAX` reached (FREE: 3); nothing saved | Inline + upgrade |
| 409 | `ENTRY_DEVIATION_REFUSED` | MSG52 | TP-C: MARKET with `activate: true` beyond the limit or at/past the take profit; nothing saved | Banner; offer "Save as Draft" |
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
      "createdAt": "2026-10-03T02:20:00Z", "activatedAt": null, "expiresAt": "2026-10-10T02:20:00Z",
      "positionStatus": null
    }
  ],
  "page": 1, "pageSize": 20, "total": 1
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/MSG15 | Bad enum, UUID, instant, paging |

FE notes: no symbol in rows — resolve `pairId` from data you already hold (FEQ-01). `positionStatus`
(T-048a): `OPEN` or `CLOSED` on an `EXECUTED` row, `null` on every other status — show it in the
Executed tab. The live P/L is not in the row (read the detail). Keep the tab in the URL.
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
  "capital": "1000.00000000", "riskPercent": "1",
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
  "statusHistory": [ { "status": "DRAFT", "at": "2026-10-03T02:20:00Z" } ],
  "position": null
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Unknown id or another user's plan (never 403) |

FE notes: show Edit only when `editable`. Activate for DRAFT; Cancel for DRAFT and ACTIVE. The
position block (SRS 3.5.3, T-041) is `position`, see "Position of an executed plan (T-048a)"; it is
read on request (refetch to refresh the P/L; no push yet).
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
| 400 | `ENTRY_DEVIATION_CONFIRMATION_REQUIRED` | MSG51 | TP-C: as `POST /plans`; the draft keeps its earlier values | Dialog; resend with `"confirmDeviation": true` |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | FUTURES on FREE | Dialog |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's plan, or pair no longer enabled | Inline |
| 409 | `TRADING_PLAN_STATUS_TRANSITION_INVALID` | MSG43 | Plan is not DRAFT | Reload plan |
| 409 | `TRADING_BLOCKING_WARNING` | MSG18 | `activate: true` with a BLOCKING warning | Banner |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | `activate: true` at the limit | Inline |
| 409 | `ENTRY_DEVIATION_REFUSED` | MSG52 | TP-C: as `POST /plans`; the draft keeps its earlier values | Banner |
| 409 | `DATA_CONFLICT` | MSG43 | Changed concurrently | Reload |
| 503 | `MARKET_PRICE_UNAVAILABLE` | MSG43 | MARKET, no live last price; `invalidationPrice`, or STOP with `activate: true`, and no live last price (Futures last price from TP-0) | Retry |

Source: `trading/controller/TradingPlanController.java#L124`; `trading/dto/request/UpdateTradingPlanRequest.java#L33`. Spec: SRS 3.5.1, UC-17, BR-32.

---

### POST /plans/{id}/activate
Status: IMPLEMENTED (develop)
Auth: trader (Futures: `FUTURES_ANALYSIS`)
Purpose: DRAFT → ACTIVE after re-checking with the current price and the plan limit (UC-18).

Request: no body. Query `confirmDeviation` (boolean, default `false`; TP-C): `true` once the Trader
confirmed MSG51.

Response `200`: `TradingPlanResponse` (`status: "ACTIVE"`, new snapshot).

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/15/16 | Inputs no longer pass (e.g. MARKET price moved past the stop → `errors.stopLoss` MSG16); a STOP already triggered → `errors.entryPrice` MSG16; the invalidation price now on the wrong side → `errors.invalidationPrice` MSG16; TP-B: a LIMIT whose take profit the last price reached → `errors.takeProfit` MSG16, a STOP whose stop loss it reached → `errors.stopLoss` MSG16; expiry already passed → MSG01 | Fields / banner; offer Edit |
| 400 | `ENTRY_DEVIATION_CONFIRMATION_REQUIRED` | MSG51 | TP-C: MARKET entry 0.25R up to the limit from the planned entry; body in "Entry deviation at MARKET activation (TP-C)" | Dialog; resend with `?confirmDeviation=true` |
| 409 | `ENTRY_DEVIATION_REFUSED` | MSG52 | TP-C: MARKET entry beyond the limit, or at/past the take profit; even with the flag | Banner; offer Edit or Cancel |
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

### PATCH /plans/{id}/position-levels
Status: PLANNED (contract fixed, TP-E)
Auth: trader
Purpose: Change the stop loss and/or take profit of the caller's OPEN position (D-124, SCR-18).

See "Edit the stop loss and take profit of an open position (TP-E)" above.
Source: `trading/controller/PositionLevelController.java`. Spec: UC-21, BR-22, BR-28, BR-29, D-124.

### POST /plans/{id}/close-position
Status: PLANNED (spec only)
Auth: trader
Purpose: Close an open simulated position at the current last price (UC-21, SCR-19, MSG21).

No code. Depends on the matching engine (T-042…T-046). Shape unknown; TD 8 lists only the path.
Source: none. Spec: TD 8, SRS 3.5.3, UC-21, BR-39.
