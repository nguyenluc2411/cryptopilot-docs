# Changelog — FE integration guide

Newest first. Each entry names the `develop` SHA the guide was synced to.

## 2026-10-25 — T-048b exits of a position, branch `feat/t-048b-journal-exits`

**Huy — visible change for the web (from `develop` `9076ca9`, not merged yet; T-041, T-047, T-059):**

- **Positions close by themselves now**: take profit, stop loss, and on Futures liquidation by the
  mark price. `position.status` becomes `CLOSED`; the plan stays `EXECUTED`.
- **New fields in `position`** (CLOSED only, `null` while OPEN): `exitPrice`, `exitTime`,
  `closeReason`, `realizedPnl`, `feeAmount`, `fundingFeeAmount`, `netPnl`, and `provisional` (boolean,
  `false` while OPEN). Show realized, fees, funding and net separately; tag net as provisional when
  `provisional` is true.
- `position.liquidationPrice` is now the position's own, computed at the fill price (it was the
  snapshot's estimate, which can differ after slippage or a gap).
- **New push** `/user/queue/positions` (`PositionUpdate`) when a position closes, and
  `/user/queue/notifications` is now admitted (Q-75): the bell can subscribe instead of polling.
- **New activation refusal:** a stop loss the last price has already reached is 400 MSG16 on
  `stopLoss` for LIMIT, STOP and MARKET (Activate and Save and Activate).
- **Notifications** MSG23 / MSG24 with the net P/L.
- A closed position frees its `ACTIVE_PLAN_MAX` slot and leaves TOTAL_OPEN_RISK.
- `modules/trading-plan.md`: new section "Exits of a position (T-048b)"; `PositionResponse` type.
  `05-realtime.md`: the two user queues and the `PositionUpdate` payload.

## 2026-10-25 — TP-D account capital, branch `feat/tp-d-account-capital`

**Huy — BREAKING change for the web (from `develop` `5f29dc6`, not merged yet):**

- **The capital input on SCR-17 must become read-only.** Show the profile's `defaultCapital` with a
  link to SCR-07 (Profile & Settings). The Trader no longer types a capital per plan (D-121).
- **`capital` is removed from the request** of `POST /plans/calculate`, `POST /plans` and
  `PUT /plans/{id}`. If the web still sends it, it is ignored: the plan is sized on the profile's
  capital, not on the typed value. Remove the field from the form state and the request types.
- **`capital` stays in the responses** (`PlanCalculationResponse`, `TradingPlanResponse`) for display.
- **New error path:** a profile without `defaultCapital` (or ≤ 0) answers 400 `errors.capital` =
  MSG01 on calculate, create, update **and activate**. Show it on the read-only capital field with the
  SCR-07 link.
- Activation recalculates the plan on the profile capital of that moment, so an ACTIVE plan may show
  a different `capital`, quantity and risk than its draft. TOTAL_OPEN_RISK divides by the current
  profile capital.
- `riskPercent` is unchanged: per plan, pre-filled from the profile.
- `modules/trading-plan.md`: new section "Account capital (TP-D)"; `PlanInputs`, input rules and the
  `/plans/calculate` example updated.

## 2026-10-25 — T-048a position of an executed plan, branch `feat/t-048a-journal-open`

**Huy — visible change for the web (from `develop` `dccfc6c`, not merged yet; T-041 uses it):**

- **`GET /plans/{id}`** (and the create / update / activate / cancel responses) carry a new
  `position` block once the plan is `EXECUTED`: `status` (`OPEN` / `CLOSED`), `fillPrice`,
  `quantity`, `entryTime`, `entryFee`, `liquidationPrice` (Futures, from the snapshot),
  `currentPrice` and `unrealizedPnl` (OPEN only: Futures mark price, Spot last price, no fees, Q-55).
  `null` before the fill. This is the SCR-18 live position block.
- **`GET /plans`** rows carry `positionStatus`: `OPEN` / `CLOSED` on `EXECUTED` rows, `null`
  otherwise (the Executed tab of SCR-16).
- An open position now keeps its `ACTIVE_PLAN_MAX` slot (MSG27) and adds its risk to the
  TOTAL_OPEN_RISK warning. Before, an EXECUTED plan freed its slot.
- No exits yet (T-048b): positions stay `OPEN`.
- `modules/trading-plan.md`: new section "Position of an executed plan (T-048a)"; `GET /plans` and
  `GET /plans/{id}` examples and notes.

## 2026-10-25 — TP-C entry deviation at MARKET activation, branch `feat/tp-c-entry-deviation`

**Huy — visible change for the web (stacked on TP-B, not merged yet; T-113 depends on it):**

- **MARKET Activate and Save and Activate** now check how far the expected fill moved from the
  plan's `plannedEntryPrice`, in R (positive = worse). Below 0.25R nothing changes.
- **New 400 `ENTRY_DEVIATION_CONFIRMATION_REQUIRED` (MSG51)** from 0.25R up to and including the
  limit (0.75R, or the plan's stricter `maxEntryDeviationR`). The body carries, as decimal strings,
  `deviationR`, `maxDeviationR`, `expectedFillPrice`, `positionQuantity`, `riskRewardRatio`,
  `netRiskReward`, and `messageArgs` = `[deviation, quantity, rr]` for the MSG51 sentence: show the
  dialog without a second call. Nothing is saved or activated.
- **Retry with the confirmation:** `POST /plans/{id}/activate?confirmDeviation=true`; for Save and
  Activate (`POST /plans`, `PUT /plans/{id}`), the same body plus `"confirmDeviation": true` (new
  optional field of `PlanInputs`).
- **New 409 `ENTRY_DEVIATION_REFUSED` (MSG52)** above the limit, or with the expected fill at or past
  the take profit (`takeProfitReached: true`), also with the confirmation. Body: `deviationR`,
  `maxDeviationR`, `expectedFillPrice`, `takeProfitReached`, `messageArgs` = `[deviation, max]`. A
  MARKET plan past its take profit got 400 MSG16 on `errors.takeProfit` before; it now gets MSG52.
- MSG16, MSG18 and MSG27 still answer first. LIMIT and STOP plans are not checked.
- `modules/trading-plan.md`: new section "Entry deviation at MARKET activation (TP-C)" with the two
  bodies and the BTC example; `PlanInputs.confirmDeviation`; the tables of `POST /plans`,
  `PUT /plans/{id}` and `POST /plans/{id}/activate`.

## 2026-10-25 — TP-B STOP trigger and invalidation, branch `feat/tp-b-stop-invalidation`

**Huy — visible change for the web (stacked on TP-0, not merged yet):**

- **STOP can be shown in the web (T-040)** once TP-B is on `develop`: the engine triggers an ACTIVE
  STOP when the last price reaches the stop (LONG ≥, SHORT ≤) and fills it at the stop, or at the
  1-minute candle's open on a gap, moved by `SLIPPAGE_BPS` against the Trader, as taker. A resting
  LIMIT still fills at its own price, as maker.
- Plans now become `INVALIDATED` on their own (`TAKE_PROFIT_REACHED` for LIMIT, `STOP_LOSS_REACHED`
  for STOP, `INVALIDATION_PRICE`), and `EXECUTED` for STOP; refetch the list and detail. The
  notification MSG54 is T-046.
- Activate and Save and Activate: new 400 MSG16 on `errors.takeProfit` (LIMIT, take profit already
  reached by the last price) and `errors.stopLoss` (STOP, stop loss already reached).
- `modules/trading-plan.md`: new section "Engine: STOP trigger and invalidation (TP-B)", activate
  errors updated; `04-enums.md`: `STOP` and `INVALIDATED` notes.

## 2026-10-24 — TP-0 fees in the risk panel, Futures last price, slippage, branch `feat/tp-0-realism`

**Huy — visible change for the web (stacked on TP-A and T-045, not merged yet):**

- Plan snapshot (`/plans/calculate`, create, update, detail): seven new decimal strings,
  `estimatedEntryFee`, `estimatedStopLossExitFee`, `estimatedTakeProfitExitFee`,
  `estimatedSlippage`, `lossAtStopLoss`, `feeShareOfRisk`, `netRiskReward`; `null` on plans saved
  before. Show **"Real loss at stop loss"** (`lossAtStopLoss`) next to the risk amount and **"R:R
  after fees"** (`netRiskReward`) next to R:R, with a tooltip saying they include the trading fees
  and slippage but not funding or the liquidation fee. The quantity is unchanged.
- `POST /plans/calculate`: new `expectedFillPrice` (MARKET only, `null` otherwise): the reference
  price `entryPrice` moved by `SLIPPAGE_BPS` against the Trader, the price the quantity is sized on;
  equal to `entryPrice` while the setting is 0. The plan detail, the create/update/activate responses
  and the list rows carry the same pair for a MARKET plan: `entryPrice` = the reference price (the
  planned entry), `expectedFillPrice` = the price the quantity was sized on; LIMIT and STOP keep
  `entryPrice` and answer `expectedFillPrice: null`.
- New warning `HIGH_FEE_SHARE` (WARNING, never blocks): fees and slippage ≥ 20 % of the risk.
  `04-enums.md` updated.
- Futures: MARKET plans are priced at the Futures last price (was the mark price); a Futures plan
  with an `invalidationPrice` and a Futures STOP activation no longer answer 503 MSG43 while a last
  price is current.
- `modules/trading-plan.md`: new section "Fees and slippage in the risk panel (TP-0)", types and
  examples updated.

## 2026-10-24 — T-107 plan gates on analysis and Futures data, branch `feat/t-107-analysis-gates`

**Huy — visible change for the web (CR-08 locks, D-60):**

- `GET /analysis/{market}/{symbol}`: new field `componentsLocked: boolean`. On FREE it is `true` and
  both `components` and `setupScore.components` are `null` (the total score stays); show the
  component rows locked with the upgrade prompt, not "Insufficient data". Futures on FREE is 403
  MSG29. PRO and PREMIUM unchanged apart from `componentsLocked: false`. The top-level `components`
  is kept (not dropped).
- `GET /market/futures/{symbol}/metrics`: 401 MSG44 without a token, 403 MSG29 on FREE.
- `GET /market/futures/{symbol}/stats`: still public; `openInterest`, `longShortRatio` and
  `lastFundingSettlement` are `null` for a Guest or FREE. Send the token on both Futures endpoints.
- `modules/market.md` updated (common rules, the three endpoints). Not merged yet: until then
  `develop` keeps answering everything to every Trader.

## 2026-10-24 — TP-A follow-up, branch `feature/TP-A-plan-validity`

- `modules/trading-plan.md`: `setupScoreAtPlan` is usually null for an activation right after a
  candle closes, until the indicator job has written that candle's row (seconds); null is not an
  error. STOP stays hidden in the web until TP-B, since the engine does not trigger STOP entries yet.
- `08-waiting-on-backend.md`: the TP-A rows no longer say Q-74 is open; PR #66 is open with one
  approval.

## 2026-10-23 (later) — TP-A setup score on the preset's timeframe, branch `feature/TP-A-plan-validity`

- `modules/trading-plan.md`: Q-77 answered again by the team lead: `setupScoreAtPlan` is read on
  the preset's own timeframe (SCALPING 15m, DAY_TRADING 1h, SWING 4h), the same score the Setup Score
  card of `GET /analysis` shows, not on `analysisTimeframe`; `analysisTimeframe` stays the plan's
  chart timeframe and the timeframe of the fill indicators. Replaces the entry below on this point.

## 2026-10-23 — TP-A review fixes, branch `feature/TP-A-plan-validity` (on `develop` @ `612b201`)

- `modules/trading-plan.md`: Q-77 answered; a plan on another timeframe than its preset's now gets a
  score; null score cases rewritten; `setupScorePreset` may be null when the read failed.
- `POST /plans/calculate` now answers 400 MSG01 on `invalidationPrice` for a MARKET plan carrying
  one, as create does.

## 2026-10-23 — TP-A plan validity, branch `feature/TP-A-plan-validity` (on `develop` @ `612b201`)

- `modules/trading-plan.md`: every request and response field TP-A adds, from the branch (not merged
  yet): `entryType` `STOP`; `invalidationPrice`, `maxEntryDeviationR`, `analysisTimeframe` in the
  request and the plan; `plannedEntryPrice`; status `INVALIDATED` with `invalidationReason` (plan and
  list row, plus `invalidatedAt` in the row); `setupScoreAtPlan` and `setupScorePreset`, now taken at
  activation from the latest closed candle (Q-74 answered). New section "Plan validity (TP-A)" with the
  rules, the MSG16 and 503 MSG43 cases (every Futures plan with an invalidation price or a Futures
  STOP activation answers 503 MSG43 until TP-0), and the null score cases (Q-77).
- Input rules and the 400/409/503 rows of create, update and activate updated; the
  `CANCELLED_EXPIRED` tab also lists INVALIDATED.
- `04-enums.md`: `STOP`, `INVALIDATED` and the new `InvalidationReason`.

## 2026-10-23 — requests to the backend, `develop` @ `796f408`

- `08-waiting-on-backend.md` rewritten as the list of requests to the backend: defects Q-75
  (notification queue refused by the STOMP guard) and Q-76 (concurrent opening of a moderation case)
  with cause, fix and test; Q-70; admin and TP-A branches to push; FEQ-02, M-09 re-checked; rows
  done since 2026-10-13 (FEQ-01, demo trading, community, notification read API) moved to its
  section 5.
- `07-open-questions.md` section E points to `08`. Only these two files and the T-065 row of
  `06-task-map.md` (D-111 of the web renumbered D-113) were touched; the rest of the guide stays
  synced to `0d92def`.

## 2026-10-08 — re-sync, `develop` @ `0d92def`

- Alerts (T-054, PR #44) and the `expectedAlertCount` check of `DELETE /watchlist/{id}` are on
  `develop`: statuses and sources moved from the branch to `develop`. 41 REST endpoints implemented.
- Alert evaluation: PRICE alerts fire since T-055 (PR #51); INDICATOR alerts are not evaluated (T-110).
- CORS for REST and `/ws` from one list, `CORS_ALLOWED_ORIGINS` (D-83, PR #50): 01-setup and
  05-realtime rewritten; M-02 and M-03 resolved; the proxy is optional.
- `PATCH /watchlist/{id}`: `sortOrder` 0–10000, MSG15 outside.
- 12 moved line references updated (`SecurityConfig`, `WebSocketConfig`, `application.yml`,
  `UpdateWatchlistItemRequest`, `WatchlistController`, `WatchlistServiceImpl`).
- Added M-15 (MSG50 means two things; Q-66). Task map points to `CURRENT_STATE.md` for FE status (D-90).

## 2026-10-03 — first version, `develop` @ `6137e24`

- Added the guide: README, setup, auth, conventions, enums, realtime, module files (auth, user,
  market, watchlist, trading-plan, planned), task map, open questions.
- Endpoints: 35 implemented on `develop`; 6 alert endpoints and the `expectedAlertCount` parameter
  of `DELETE /watchlist/{id}` pending on `feat/t-054-alert-rules` @ `0803903`; 43 planned in TD 8
  plus 13 admin areas.
- Raised FEQ-01…FEQ-05 and recorded mismatches M-01…M-14 in `07-open-questions.md`.
- Placed under `docs/design/fe-guide/` (not `docs/fe-guide/`) because `docs/design/` is already in
  the local-only exclude list of every clone, so the guide cannot show up as untracked in the public
  code repository.
