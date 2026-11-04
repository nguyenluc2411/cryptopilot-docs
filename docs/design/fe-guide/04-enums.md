# 04 · Enums

Every enum that appears in a request or response. Values are exact (upper case, case-sensitive in
JSON bodies and in enum-typed query parameters). Labels are suggestions for English UI.

Code path prefix: `backend/src/main/java/com/cryptopilot/`.

## Identity and profile

### `UserRole` — `SessionResponse.role`

| Value | Meaning | UI label |
|---|---|---|
| `TRADER` | Self-registered user | Trader |
| `ADMIN` | Administrator (only an admin grants it) | Admin |

Source: `user/model/enums/UserRole.java#L25`.

### `TradingStyle` — profile

| Value | Meaning | UI label | Setup score preset it selects (T-109) |
|---|---|---|---|
| `SCALPING` | Minutes; many trades a day | Scalping | `SCALPING` (15m) |
| `DAY` | Hours; within one session | Day trading | `DAY_TRADING` (1h) |
| `SWING` | Days to weeks | Swing | `SWING` (4h) |
| `POSITION` | Weeks to months | Position | `SWING` (4h) until a POSITION preset exists |
| `null` | Not chosen | Not set | `DAY_TRADING` (1h) |

Source: `user/model/enums/TradingStyle.java#L11`. Spec: SRS 3.2.5, D-53.

### `RiskProfile` — profile, risk profile, questionnaire suggestion

| Value | Risk per trade | Max Futures leverage | Max total open risk | UI label |
|---|---|---|---|---|
| `CONSERVATIVE` | 0.5 % | 3x | 2 % | Conservative (default, D-64) |
| `BALANCED` | 1 % | 5x | 4 % | Balanced |
| `AGGRESSIVE` | 2 % | 10x | 6 % | Aggressive — needs MSG48 confirmation |

Numbers are configuration (`cryptopilot.user.risk-profiles`); read them from
`GET /me/risk-profile`, do not hard-code them.

Source: `user/model/enums/RiskProfile.java#L12`. Spec: BR-66, D-64.

### `QuestionGroup` — risk questionnaire

| Value | Meaning | UI label |
|---|---|---|
| `CAPACITY` | Capacity to bear financial loss | Capacity for loss |
| `ATTITUDE` | Attitude to risk | Attitude to risk |

Source: `user/model/enums/QuestionGroup.java#L8`. Spec: BR-67.

### `DevicePlatform` — devices

| Value | UI label |
|---|---|
| `ANDROID` | Android |
| `IOS` | iOS |

Source: `user/model/enums/DevicePlatform.java#L10`.

## Market

### Market (`MarketType`)

| Value | UI label |
|---|---|
| `SPOT` | Spot |
| `FUTURES` | Futures (USDⓈ-M perpetual) |

Where it appears and how it is typed:

| Place | Type | Case |
|---|---|---|
| Path `{market}` of `/market/...` and `/analysis/...`; `?market=` of `/market/pairs` | string | any case (`spot`, `SPOT`) |
| `market` field of market responses and STOMP payloads | string | `"SPOT"` / `"FUTURES"` |
| STOMP destinations | segment | `SPOT` / `FUTURES` exactly (e.g. `/topic/ticker.SPOT.BTCUSDT`) |
| Plan and alert bodies; `?market=` of `GET /plans` | enum | **upper case only** |

Source: `market/model/enums/MarketType.java#L19`.

### Timeframe (string)

`"15m"`, `"1h"`, `"4h"`, `"1d"` (BR-08) — exact lower-case codes. Default for analysis `1h`. The
`MarketInterval` enum also has `1m` and `5m`, which the API refuses.

Source: `market/model/enums/MarketInterval.java#L16`.

### `SetupStyle` — `setupScore.preset`

| Value | Timeframe | UI label |
|---|---|---|
| `SCALPING` | 15m | Scalping |
| `DAY_TRADING` | 1h | Day trading |
| `SWING` | 4h | Swing |

Show with `presetVersion`, e.g. "Day trading v1" (D-53).

Source: `market/model/enums/SetupStyle.java#L8`.

### `DominantSide` — Futures `setupScore.dominantSide`

| Value | UI label |
|---|---|
| `LONG` | Long bias |
| `SHORT` | Short bias |
| `NEUTRAL` | Neutral |

Shown next to the score, not part of it (BR-13). `null` when it cannot be computed.

Source: `market/model/enums/DominantSide.java#L8`.

## Trading plan

### `Direction`

| Value | UI label | Note |
|---|---|---|
| `LONG` | Long | Only value allowed on Spot (BR-21) |
| `SHORT` | Short | Futures only |

Source: `trading/model/enums/Direction.java#L8`.

### `EntryType`

| Value | UI label | Note |
|---|---|---|
| `LIMIT` | Limit | `entryPrice` required; expiry defaults to 7 days |
| `MARKET` | Market | Entry = current last price; `entryPrice` ignored |
| `STOP` | Stop (breakout) | `entryPrice` = stop price, required; expiry defaults to 7 days; triggered by the last price from TP-B, fills at the stop or at the candle open on a gap, taker, with slippage |

Source: `trading/model/enums/EntryType.java#L8`.

### `MarginMode`

| Value | UI label |
|---|---|
| `ISOLATED` | Isolated (fixed, BR-26) |

Source: `trading/model/enums/MarginMode.java#L9`.

### `PlanStatus`

| Value | Meaning | UI label | Badge colour (suggestion) |
|---|---|---|---|
| `DRAFT` | Saved, editable; can be activated or cancelled | Draft | grey |
| `ACTIVE` | Waiting for its entry; can be cancelled, filled, or expire | Active | blue |
| `EXECUTED` | Entry filled; the position lives in the journal. Terminal | Executed | green |
| `CANCELLED` | Cancelled by the Trader. Terminal | Cancelled | dark grey |
| `EXPIRED` | Expiry passed before a fill. Terminal | Expired | amber |
| `INVALIDATED` | TP-A branch. The setup ended before the entry filled (see `InvalidationReason`). Terminal | Invalidated | amber |

Transitions: `DRAFT → ACTIVE | CANCELLED`; `ACTIVE → EXECUTED | CANCELLED | EXPIRED | INVALIDATED`. Nothing leaves a
terminal status. `EXECUTED` and `EXPIRED` are set by the matching engine (T-042+), not by the client.

`INVALIDATED` is set by the matching engine (TP-B branch), see `modules/trading-plan.md` "Engine: STOP trigger and
invalidation (TP-B)".

Source: `trading/model/enums/PlanStatus.java#L19`. Spec: BR-32, BR-68, D-66, D-111.

### `InvalidationReason` (TP-A branch)

| Value | Meaning |
|---|---|
| `TAKE_PROFIT_REACHED` | A LIMIT plan's take profit was reached first |
| `STOP_LOSS_REACHED` | A STOP plan's stop loss was reached first |
| `INVALIDATION_PRICE` | The plan's own `invalidationPrice` was reached |

Source: `trading/model/enums/InvalidationReason.java`. Spec: BR-68, D-111.

### `PlanTab` — `?tab=` of `GET /plans`

| Value | Statuses | UI tab |
|---|---|---|
| `DRAFT` | DRAFT | Draft |
| `ACTIVE` | ACTIVE | Active |
| `EXECUTED` | EXECUTED | Executed |
| `CANCELLED_EXPIRED` | CANCELLED, EXPIRED, INVALIDATED (TP-A) | Cancelled / Expired |

Source: `trading/model/enums/PlanTab.java#L11`. Spec: SRS 3.5.2, D-73.

### `WarningSeverity`

| Value | UI | Blocks activation |
|---|---|---|
| `INFO` | Info (blue) | No |
| `WARNING` | Warning (amber) | No |
| `BLOCKING` | Blocking (red) | **Yes** — MSG18 |

Source: `trading/model/enums/WarningSeverity.java#L9`.

### `WarningType`

The server also sends `message`, a short English sentence for developers (e.g. `"leverage 12x is
above the risk profile's maximum of 10x"`). Build the user text from `type` with the client's own
wording; show `message` only as a detail if at all.

| Value | Severity | Meaning (BR-28, BR-29) | Suggested UI text |
|---|---|---|---|
| `INSUFFICIENT_CAPITAL` | BLOCKING | Margin / cost is above the capital | Not enough capital for this position |
| `SL_BEYOND_LIQUIDATION` | BLOCKING | Stop loss at or beyond the estimated liquidation price (Futures) | Stop loss is beyond the liquidation price |
| `LOW_RR` | WARNING | Reward/risk below `WARN_LOW_RR_RATIO` (1.5) | Low reward-to-risk ratio |
| `OVERSIZED_POSITION` | WARNING | Risk % above the profile's risk per trade | Risk per trade above your profile |
| `HIGH_LEVERAGE` | WARNING | Leverage above the profile's maximum | Leverage above your profile |
| `TOTAL_OPEN_RISK` | WARNING | This plan + other ACTIVE plans above the profile's max open risk | Total open risk above your profile |
| `WIDE_STOP_LOSS` | INFO | Stop farther than `WARN_WIDE_STOP_LOSS_PERCENT` (10 %) from entry | Wide stop loss |
| `HIGH_FUNDING_RATE` | WARNING | Funding rate magnitude above `WARN_HIGH_FUNDING_RATE` (0.001) and paid by this side (Futures) | High funding rate for this side |
| `HIGH_FEE_SHARE` | WARNING | Expected fees and slippage at the stop loss are at least `FEE_RISK_WARN_RATIO` (0.20) of the risk amount (TP-0, D-116; never blocks) | Fees and slippage are {feeShareOfRisk × 100}% of your risk |

Thresholds are system settings; the numbers above are the seed values and can change.

Source: `trading/model/enums/WarningType.java#L9`. Spec: BR-28, BR-29 (nine types since D-116), Q-27.

## Alerts

On `develop` since PR #44 (T-054); unchanged since the branch read at `0803903`.

### `AlertType`

| Value | Meaning | UI label |
|---|---|---|
| `PRICE` | Last price of the selected market | Price |
| `INDICATOR` | One of `AlertIndicator`; PRO/PREMIUM only | Indicator |

### `AlertIndicator`

| Value | Market | Timeframe | Threshold | Condition | UI label |
|---|---|---|---|---|---|
| `RSI_14` | both | required (15m/1h/4h/1d) | required, 0–100 | any | RSI (14) |
| `MACD_CROSS` | both | required | must be absent | `CROSS_ABOVE`/`CROSS_BELOW` only | MACD crosses signal |
| `EMA_CROSS` | both | required | must be absent | `CROSS_ABOVE`/`CROSS_BELOW` only | EMA20 crosses EMA50 |
| `FUNDING_RATE` | FUTURES only | must be absent (server sets 1h) | required (unit open, Q-30) | any | Funding rate |
| `OPEN_INTEREST_CHANGE` | FUTURES only | must be absent (server sets 1h) | required, % change over 1 h | any | Open interest change (1h) |

### `ConditionOperator`

| Value | Meaning | UI label |
|---|---|---|
| `CROSS_ABOVE` | Previous below threshold, now at/above | Crosses above |
| `CROSS_BELOW` | Previous above threshold, now at/below | Crosses below |
| `GREATER_THAN` | Now above | Greater than |
| `LESS_THAN` | Now below | Less than |

For MACD_CROSS / EMA_CROSS, `CROSS_ABOVE` means the first line crosses above the second (bullish).

### `TriggerMode`

| Value | Meaning | UI label |
|---|---|---|
| `ONCE` | Fires once, then `TRIGGERED` | Once |
| `ONCE_PER_BAR` | At most once per candle of the timeframe (1h for PRICE) | Once per bar |
| `EVERY_TIME` | Each time the condition becomes true; `cooldownMinutes` ≥ 1 required | Every time |

### `AlertStatus`

| Value | Meaning | UI label | Who sets it |
|---|---|---|---|
| `ACTIVE` | Evaluated; counts against `ACTIVE_ALERT_MAX` | Active | create, resume, edit |
| `PAUSED` | Kept, not evaluated | Paused | pause |
| `TRIGGERED` | A ONCE alert fired; edit to re-activate | Triggered | alert engine (T-055) |
| `EXPIRED` | Expiry passed; edit to re-activate | Expired | alert engine (T-055) |

"Paused because of a plan change" (SRS 3.4.3) has no marker yet (Q-31).

Source: `backend/src/main/java/com/cryptopilot/watchlist/model/enums/AlertType.java#L9`,
`AlertIndicator.java#L8`, `ConditionOperator.java#L8`, `TriggerMode.java#L8`, `AlertStatus.java#L20`
(same folder).

## Administration (PR #93, `feat/uc-52-audit-log`, not merged)

PENDING PR: values from code on the branch; the FE may build SCR-44 against them behind a flag.

### `ActorType` — `?actorType=` of `GET /admin/audit-log`

| Value | Meaning | UI label |
|---|---|---|
| `USER` | An account acted | User |
| `SYSTEM` | A scheduled job or a payment callback acted (`actor: null`) | System |

### `AuditAction` — `action` of an audit entry, `?action=` (repeatable)

`ACCOUNT_LOCKED`, `ACCOUNT_UNLOCKED`, `ACCOUNT_BANNED`, `ROLE_CHANGED`, `POST_HIDDEN`,
`POST_RESTORED`, `POST_REMOVED`, `REPORTS_DISMISSED`, `USER_WARNED`, `NEWS_ARTICLE_HIDDEN`,
`NEWS_ARTICLE_RESTORED`, `COMMENT_HIDDEN`, `COMMENT_REMOVED`, `COMMENT_RESTORED`,
`CONFIGURATION_CREATED`, `CONFIGURATION_CHANGED`, `CONFIGURATION_DELETED`, and since PR #93
`AUDIT_LOG_EXPORTED` (an admin exported the audit log). Labels: the value in sentence case.

### `AuditedEntity` — `entityType` of an audit entry, `?entityType=`

`USER_ACCOUNT`, `FORUM_POST`, `FORUM_COMMENT`, `CRYPTO_PAIR`, `LEVERAGE_BRACKET`,
`SUBSCRIPTION_PACKAGE`, `SUBSCRIPTION_ORDER`, `NEWS_SOURCE`, `NEWS_ARTICLE`, `AI_CONFIGURATION`,
`SYSTEM_SETTING`, `ACADEMY_ARTICLE`, `ACADEMY_TERM`, `ACADEMY_TOPIC`, and since PR #93 `AUDIT_LOG`
(an export; `entityId` is `null`).

### `SystemEventCategory` — system log

| Value | Meaning | UI label |
|---|---|---|
| `SYSTEM_ERROR` | An unexpected 500 (with the reference the caller got) or a scheduled job that threw | System error |
| `EXTERNAL_API_FAILURE` | A call to an external service failed | External API failure |

### `SystemEventSource` — system log and health panel

| Value | Meaning | On the health panel |
|---|---|---|
| `APPLICATION` | A request answered with 500 | no |
| `SCHEDULED_JOB` | A `@Scheduled` job | no |
| `BINANCE_REST` | Binance Spot and Futures REST | yes |
| `AI_SERVICE` | The AI Service | yes |
| `MEDIA_STORAGE` | Cloudinary (forum media) | yes |
| `NEWS_SOURCE` | All RSS feeds and news pages, one row | yes |
| `MAIL` | The SMTP server | yes |

### `ServiceStatus` — `services[].status` of `GET /admin/system-health`

| Value | Meaning | UI label |
|---|---|---|
| `UP` | Answered, no failure in the last `recentWindowMinutes` (15) | Up |
| `DEGRADED` | Failed in the window, answered again after that (news: some feeds failed, others answered) | Degraded |
| `DOWN` | Failed in the window and not answered since; or Binance bans the server (`bannedUntil`) | Down |
| `UNKNOWN` | Not called since the backend started, no recent failure | Unknown |

### Bracket template id — `id` of `GET /admin/pairs/bracket-templates`

`MAJOR` (125x first bracket), `ALTCOIN` (75x), `SMALL_CAP` (50x).

Source: `admin/model/enums/ActorType.java`, `AuditAction.java`, `AuditedEntity.java`,
`SystemEventCategory.java`, `SystemEventSource.java`, `ServiceStatus.java` (same folder);
`market/model/enums/BracketTemplate.java`, branch `feat/uc-52-audit-log` at `cedc28b`.

## Plan tier (in `messageArgs` only)

`PlanTier`: `FREE`, `PRO`, `PREMIUM`. Appears as text in MSG27 / MSG29 arguments. Labels: Free, Pro,
Premium.

Source: `billing/model/enums/PlanTier.java#L12`.
