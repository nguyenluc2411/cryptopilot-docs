# WF-01 demo scenarios (DEMO-01)

Workflow WF-01: a Trader plans a trade with explicit risk, activates it, the simulated exchange fills and closes it, and
the journal records the result (UC-16…UC-21; BR-26, BR-27, BR-62, BR-66, BR-68, BR-69). Review 2 guide 9.2 requires
at least one main and one exception scenario per workflow, a demo on **staging**, and sample data **loaded by a script
from the repository**, so the demo can be repeated and the council can change the inputs.

Written 2026-10-25 (BE1), on `feat/demo-01-wf01-data` from `develop` `dccfc6c`.

## 1. Setting up the data (every time, same result)

| Step | Dev | Staging |
|---|---|---|
| Backend profile | `SPRING_PROFILES_ACTIVE=dev` | `SPRING_PROFILES_ACTIVE=prod,demo` |
| Password hashes in the backend's environment | `ADMIN_PASSWORD_HASH`, `DEMO_PASSWORD_HASH` | same |
| Wait for the pairs | NSF-01 creates them at start-up (about a minute on a fresh DB) | same |
| Load | `.\deploy\demo\load-wf01.ps1` | `pwsh deploy/demo/load-wf01.ps1 -BaseUrl https://<staging>` |
| Plain passwords for the script | `ADMIN_PASSWORD`, `DEMO_PASSWORD` in the shell | same |

Flyway applies the accounts (`db/demo/R__demo_wf01_accounts.sql`). The script loads the pairs, brackets and demo.free's
plans through the API and changes only what differs from `deploy/demo/wf01.json`. Run it again before each rehearsal
and before the defence, because it also restores a demo plan that was cancelled or a pair that was switched off.
Command details are in `deploy/README.md`.

### Data after loading

| Account (`@cryptopilot.invalid`) | Tier | Risk profile | Capital (USDT) | Risk / trade | Style | Other |
|---|---|---|---|---|---|---|
| `demo.free` | FREE (no subscription) | CONSERVATIVE | 10,000 | 1 % | — | 3 ACTIVE Spot LIMIT LONG plans (BTCUSDT, ETHUSDT, BTCUSDT), entry 50 % / SL 45 % / TP 150 % of the Spot price at load time, expiring 2027-04-01 |
| `demo.pro` | PRO (PRO_YEARLY, ACTIVE 2026-10-25 → 2027-10-25) | BALANCED | 10,000 | 1 % | DAY | — |
| `demo.premium` | PREMIUM (PREMIUM_YEARLY, same dates) | AGGRESSIVE (stored; the MSG48 confirmation is asked only when switching) | 50,000 | 1 % | — | — |

| Pair | Spot | Futures | Ceiling | Leverage brackets |
|---|---|---|---|---|
| BTCUSDT | on | on | 125x | 12 tiers, copied from Binance's public table (Binance updateTime 2025-08-19, retrieved 2026-10-25); tier 1 is 150x on Binance and is stored as 125x |
| ETHUSDT | on | on | 125x | 12 tiers, same source and date |

On dev, Q-16 also turns on the other seed symbols (20x ceiling, no brackets). The demo uses only BTCUSDT and ETHUSDT.

**Expected warnings on demo.free's plans:** 1 % per trade is above CONSERVATIVE's 0.5 %, and three plans exceed its 2 %
total open risk. Both are non-blocking warnings, so they are useful to show the BR-29 panel. They do not stop
activation.

## 2. Scenarios

Unless a step says otherwise, sign in on the web app as the account named, on the staging URL.

### DS-01a: main scenario, Futures plan to closed journal entry

- **Type:** main. **Account:** demo.pro (PRO, BALANCED).
- **Data:** BTCUSDT Futures, MARKET LONG, SL = price − 0.5 %, TP = price + 1.5 %, risk 1 % (100 USDT of 10,000),
  leverage 5 (BALANCED's maximum, so no leverage warning). Expected panel: R:R 3, notional ≈ 20,000 USDT, margin
  ≈ 4,000 USDT, liquidation ≈ 19–20 % below the entry, so far beyond the SL.
- **Steps:** SCR-17, enter the values → panel → *Save and Activate* → the plan fills at once (MARKET, BR-33) → open
  position on SCR-18 → *Close position* (manual close) → SCR journal.
- **Expected:** plan EXECUTED with a fill price, fill liquidity TAKER and the slippage of TP-0. After the close, a journal
  entry CLOSED with the realised PnL, entry and exit fees, the funding settled while open, and net = realised − fees −
  funding.
- **Proved by:** `TradingPlanServiceImplTest.BR33_aMarketPlanActivated_isFilledAtOnce_andNeverWaitsInTheBooks`,
  `TradingPlanApiTest.D111_aFuturesMarketPlan_fillsAtTheLastPrice_notTheMarkPrice` (develop);
  `TradeResultCalculatorTest` (realised, fees and net of a manual close, develop); journal OPEN on fill: T-048a
  (BE2 branch `feat/t-048a-journal-open`, not merged).
- **Not demonstrable yet:** manual close is T-046 and the CLOSED journal record is T-048b/c. Until they merge, the demo
  stops at the open position. The end-to-end test of this scenario belongs to those tasks.

### DS-01b: main scenario, LIMIT plan waiting in the book

- **Type:** main. **Account:** demo.pro.
- **Data:** BTCUSDT Spot (or Futures), LIMIT LONG with entry ≈ price − 1 %, SL ≈ entry − 1 %, TP ≈ entry + 3 %, and an
  invalidation price above the current price (for example price + 2 %).
- **Steps:** SCR-17 → *Save and Activate*.
- **Expected:** plan ACTIVE, no fill (the price has not reached the entry), status history DRAFT → ACTIVE, expiry 7
  days by default. An invalidation price on the wrong side of the current price is MSG16 on that field.
- **Proved by:** `TradingPlanServiceImplTest.BR33_BR68_activatingALimitWithAnInvalidationPrice_readsTheLastPriceOnce`
  (last 101 → ACTIVE), `…BR68_theInvalidationPrice_mustLieOnTheFarSideOfTheCurrentPrice_elseMsg16OnItsField`,
  `TradingPlanApiTest.MSG16_aWrongSideInvalidationPrice_isNamedUnderErrors` (develop).

### DS-01c: exception, stop loss beyond liquidation

- **Type:** exception (business rule). **Account:** demo.pro.
- **Data:** BTCUSDT Futures, LIMIT or MARKET LONG, leverage **50x** (allowed: tier 1 and the pair ceiling are 125x),
  SL ≈ entry − 5 %. At 50x the liquidation price is about 1.6 % below the entry (BR-26, BR-27 with tier 1 MMR 0.4 %).
- **Steps:** SCR-17 → panel → *Save and Activate*.
- **Expected:** BLOCKING warning `SL_BEYOND_LIQUIDATION` on the panel, plus a WARNING for leverage above BALANCED's 5x.
  Activation is refused with **MSG18**. *Save* as a draft is allowed and the draft keeps the warning.
- **Proved by:** `StopBeyondLiquidationRuleTest` (BR-28 boundaries), `TradingPlanTest.MSG18_aBlockingWarning_refusesActivationAndLeavesTheDraftUnchanged`,
  `TradingPlanServiceImplTest.MSG18_saveAndActivate_withABlockingWarning_isRefused`,
  `TradingPlanApiTest.MSG18_aBlockingWarning_refusesTheActivation` (develop; the API test blocks on INSUFFICIENT_CAPITAL,
  the same MSG18 path).
- **Gap:** no API test drives SL_BEYOND_LIQUIDATION itself on stored brackets. Proposed as a test-only follow-up.

### DS-01d: exception, FREE asks for Futures

- **Type:** exception (permission / plan tier). **Account:** demo.free.
- **Data:** any Futures plan on BTCUSDT.
- **Steps:** SCR-17, choose Futures → *Calculate* or *Save*.
- **Expected:** **MSG29** (feature not in the FREE plan, BR-62). Nothing is saved.
- **Proved by:** `TradingPlanApiTest.MSG29_aFreeTrader_cannotPlanOnFutures`,
  `TradingPlanServiceImplTest.MSG29_activatingAFuturesPlanWithoutTheFeature_isRefusedBeforeTheMissingLastPriceIsNoticed` (develop).

### DS-01e: exception, MARKET entry moved since the draft

- **Type:** exception (business rule BR-69). **Account:** demo.pro.
- **Data:** BTCUSDT MARKET LONG **draft**, saved with a tight SL (for example 0.1 % below the price, so 1 R ≈ 0.1 % of the
  price). The planned entry is the price at save time.
- **Steps:** wait until the price has moved by more than 0.25 R (≈ 0.025 %, usually within a minute) → *Activate* →
  MSG51 shows the recalculated quantity and R:R → *Confirm* → filled. Repeat with a fresh draft once the move is beyond
  0.75 R → *Activate* → **MSG52**, refused even with confirmation.
- **Expected:** below 0.25 R the plan activates directly. Between 0.25 and 0.75 R the result is 400 MSG51 until
  confirmed. Above 0.75 R it is 409 MSG52. The thresholds are the `system_setting` values, changed only through the
  admin API.
- **Proved by:** `TradingPlanApiTest.MSG51_aMarketEntryHalfAnRFromThePlan_answersTheRecalculatedPlan_untilConfirmed`,
  `…MSG52_aMarketEntryOneRFromThePlan_isRefused_evenWhenConfirmed`, `…MSG51_saveAndActivate_isConfirmedInTheBody`,
  `EntryDeviationCalculatorTest` (TP-C, BE1 branch `feat/tp-c-entry-deviation`, not merged).
- **Note:** the live move cannot be scheduled. If the market is too calm on the day, show the automated test instead.

### DS-01f: LIMIT invalidated when the TP is reached first

- **Type:** exception (business rule BR-68). **Shown by the automated replay test**, not live, because a live demo would
  need the market to reach the TP before the entry.
- **Data / steps:** `MatchingReplayTest` (TP-B) replays closed 1-minute candles over a crash and restart. Plan
  `limitLong96` is a LIMIT LONG whose TP is reached before its entry and ends **INVALIDATED** with reason
  `TAKE_PROFIT_REACHED` at minute 6, identical to live processing. Run
  `./mvnw -Dtest=MatchingReplayTest test` and show the plan's status and `invalidation_reason`.
- **Proved by:** `MatchingReplayTest.T043_aCrashAndRestartReplay_fillsEveryPlanAsLiveProcessingDoes`,
  `MatchingEngineTest.BR68_aLimitWhoseTakeProfitIsReachedFirst_isInvalidated_andLeavesBothBooks`,
  `MatchingWorkerTest.BR68_aRangeReachingTheTakeProfitFirst_invalidatesTheLimitPlan` (TP-B, PR #70, not merged).

### DS-01g: exception, FREE's fourth ACTIVE plan

- **Type:** exception (plan limit BR-62). **Account:** demo.free (already holds 3 ACTIVE plans from the loader).
- **Data:** any Spot LIMIT plan on BTCUSDT or ETHUSDT.
- **Steps:** SCR-17 → *Save and Activate* (or *Save*, then *Activate* on SCR-16).
- **Expected:** **MSG27** with the limit 3 and the FREE tier. With *Save and Activate* nothing is saved; with a saved
  draft the draft stays DRAFT. demo.pro (PRO, no limit) activates the same plan.
- **Proved by:** `TradingPlanApiTest.MSG27_aFreeTraderWithThreeActivePlans_cannotActivateAFourth`,
  `TradingPlanServiceImplTest.MSG27_saveAndActivate_overThePlanLimit_savesNothing` (develop);
  the starting state by `DemoLoaderTest.DEMO01_loadingTwice_setsTheDemoUpOnceAndThenChangesNothing` (DEMO-01).

## 3. Readiness on `develop` today

| Scenario | Live demo possible on develop | Waiting for |
|---|---|---|
| DS-01a | up to the open position | T-046 (manual close), T-048a/b/c (journal) |
| DS-01b, DS-01c, DS-01d, DS-01g | yes | — |
| DS-01e | no | TP-C merge |
| DS-01f | no (replay test) | TP-B merge (PR #70) |

## 4. Tests of the demo data itself (DEMO-01)

| Test | Proves |
|---|---|
| `DemoDatasetTest` | accounts, tier on a defence day and back on FREE at the end, risk profile, capital, risk, style; re-applying the SQL changes nothing; the data file's pairs and brackets (contiguous, MMR in (0, 1), leverage never rising, BR-27 amount) pass the administrator's own service, and a bracket off by 1 is rejected |
| `DemoProfileTest` | only `dev` and `demo` list `db/demo`; base and `prod` do not |
| `DemoLoaderTest` | the script against a backend on the `demo` profile: first load sets everything up, the second changes nothing (audit trail included); restores a cancelled plan and a changed pair; waits for a first price; stops on a missing pair, a missing price, missing passwords and a data file naming an unknown pair |
