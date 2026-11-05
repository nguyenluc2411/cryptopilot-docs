# Planned modules (spec only)

Everything in this file is **PLANNED (spec only)**: listed in TD 8 or SRS, with no controller or DTO
in code. Do not call these paths; until a controller exists a Guest gets 401, a TRADER
404 (no handler) and an ADMIN 403. Request and response shapes are not defined — do not invent them. What the spec does fix
(paths, roles, plan gates, messages) is listed so screens can be laid out.

Common to all: TRADER only unless stated; paging, errors and dates follow `03-conventions.md`.
Source for every entry: no code at `6137e24`; TD 8 endpoint catalogue.

## journal — SCR-20 … SCR-23 (T-048 … T-052)

### GET /journal
Status: PLANNED (spec only)
Auth: trader
Purpose: List journal entries, filter by source SIMULATED / MANUAL (UC-22).
Request: not defined. Response: not defined. Errors: not defined.
FE notes: paged (CR-04). Source filter separates simulated from manual (T-052).
Source: none. Spec: TD 8, SRS 3.6.1, UC-22, BR-40.

### GET /journal/{id}
Status: PLANNED (spec only)
Auth: trader
Purpose: One journal entry (SCR-21).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.6.1.

### PUT /journal/{id}
Status: PLANNED (spec only)
Auth: trader
Purpose: Write the trade review (UC-23). Execution facts of SIMULATED entries are immutable.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.6.1, UC-23, BR-40.

### POST /journal/manual
Status: PLANNED (spec only)
Auth: trader
Purpose: Record a manual trade (UC-24).
Request/Response/Errors: not defined. Validation of times and price order (BR-41).
Source: none. Spec: TD 8, SRS 3.6.2, UC-24, BR-41.

### DELETE /journal/{id}
Status: PLANNED (spec only)
Auth: trader
Purpose: Delete a MANUAL entry only.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8.

### GET /journal/performance/* (T-051, SCR-23, SCR-08 widget)
Status: BUILT on `feat/t-051-performance-stats`, not merged. The path replaces the planned `GET /performance`.
Auth: trader (guest 401, admin 403); only the caller's closed trades.
Filters, the same on all five, all optional: `from`, `to` (`yyyy-MM-dd`, UTC+7 days, `from` counted and `to` not, at most one year; default the year up to and including today), `market` (`SPOT`, `FUTURES`, `ALL`; default `ALL`), `source` (`SIMULATED`, `MANUAL`, `ALL`; default `SIMULATED`, BR-41), `pairId`, `strategyId`. A bad filter answers 400 MSG01; a bad period names `from` or `to` with MSG15.
Decimals are strings with 8 decimals. A ratio or mean with nothing to compute is `null`, never 0: show a dash.

`GET /journal/performance/summary`, every plan:
`from, to, trades, wins, losses, breakeven, winRate (0 to 1), totalNetPnl, provisionalTrades, advanced`. `trades: 0` is the empty result: show MSG41 (it is 200, not 404). `provisionalTrades > 0`: the total may still change, funding is incomplete. `advanced` is `null` on FREE: show the locks (CR-08), do not call it an error.
`advanced` on PRO and PREMIUM: `averageWin, averageLoss (negative), profitFactor, averagePlannedRiskReward, averageRealizedR (also the expectancy in R), tradesWithR, largestWin, largestLoss, maxConsecutiveLosses, maxDrawdown (positive USDT), totalFees, totalFunding (+ received), averageEntryDeviationR, costOfLateEntryR, averageMaeR, averageMfeR`. The last four are `null` until T-048c stores the learning data.

`GET /journal/performance/by-coin`, `/by-strategy`, `/by-market`, PRO and PREMIUM, FREE 403 MSG29: a list, highest net P/L first, of `key, label, trades, wins, losses, breakeven, winRate, netPnl, profitFactor, averageRealizedR`. `key` is the pair id, strategy id or market; `label` the symbol, strategy name or market. Trades without a strategy: `key: null`, `label: "Unassigned"`.

`GET /journal/performance/equity-curve`, PRO and PREMIUM, FREE 403 MSG29: oldest first, one point per day with an exit: `day, trades, netPnl, cumulativeNetPnl`. The curve starts at 0 at `from`.
Source: `PerformanceController`. Spec: SRS 3.6.3, UC-25 (current SRS UC-22), BR-41, BR-42, BR-62, TD 7.10.

## community — SCR-24 … SCR-27 (T-060 … T-065)

### GET /posts
Status: PLANNED (spec only)
Auth: trader
Purpose: Community feed; official posts pinned (UC-26).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.7.1, UC-26.

### POST /posts
Status: PLANNED (spec only)
Auth: trader; video needs `VIDEO_POST` (PREMIUM) → MSG29
Purpose: Create a post with coin tags and media (UC-27, UC-28). Success MSG33.
Request/Response/Errors: not defined. Media limits MAX_IMAGES_PER_POST 4, MAX_IMAGE_SIZE_MB 5, MAX_VIDEO_SIZE_MB 100, MAX_VIDEO_DURATION_SECONDS 300 (seed values) → MSG32.
Source: none. Spec: TD 8, SRS 3.7.2, UC-27, UC-28, BR-43, BR-44.

### GET /posts/{id}
Status: PLANNED (spec only)
Auth: trader
Purpose: Post detail (SCR-25).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.7.1.

### PUT /posts/{id}
Status: PLANNED (spec only)
Auth: trader (own post)
Purpose: Edit own post (UC-29).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.7.2, UC-29.

### DELETE /posts/{id}
Status: PLANNED (spec only)
Auth: trader (own post)
Purpose: Soft-delete own post (UC-29, BR-47).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, UC-29, BR-47.

### POST /posts/{id}/like
Status: PLANNED (spec only)
Auth: trader
Purpose: Like a post; one per user (UC-31, BR-45).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.7.3.

### DELETE /posts/{id}/like
Status: PLANNED (spec only)
Auth: trader
Purpose: Remove the like.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8.

### POST /posts/{id}/save
Status: PLANNED (spec only)
Auth: trader
Purpose: Save a post (UC-32).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, UC-32.

### DELETE /posts/{id}/save
Status: PLANNED (spec only)
Auth: trader
Purpose: Unsave.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8.

### GET /posts/{id}/comments
Status: PLANNED (spec only)
Auth: trader
Purpose: Comments and replies of a post (UC-30).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.7.3.

### POST /posts/{id}/comments
Status: PLANNED (spec only)
Auth: trader
Purpose: Comment or reply (UC-30).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, UC-30.

### PUT /comments/{id}
Status: PLANNED (spec only)
Auth: trader (own comment)
Purpose: Edit own comment.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8.

### DELETE /comments/{id}
Status: PLANNED (spec only)
Auth: trader (own comment)
Purpose: Soft-delete own comment.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, BR-47.

### POST /comments/{id}/like
Status: PLANNED (spec only)
Auth: trader
Purpose: Like a comment (BR-45).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8.

### DELETE /comments/{id}/like
Status: PLANNED (spec only)
Auth: trader
Purpose: Remove the like.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8.

### POST /posts/{id}/reports
Status: PLANNED (spec only)
Auth: trader
Purpose: Report a post; one per user, not own post (UC-33, BR-46). MSG34 either text.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.7.4, UC-33, BR-46.

### POST /media/upload-signature
Status: PLANNED (spec only)
Auth: trader
Purpose: Signed upload parameters for direct upload to the media store (T-061).
Request/Response/Errors: not defined. The avatar upload (T-101) will use the same media seam; it has no endpoint in TD 8.
Source: none. Spec: TD 8, BR-44.

## news — SCR-28 (T-077 … T-080)

### GET /news
Status: PLANNED (spec only)
Auth: trader; AI summary and sentiment `NEWS_AI_INSIGHT` (PRO+)
Purpose: News feed with filters `coin`, `sentiment`, `range` (UC-34).
Request: query names from TD 8: `coin`, `sentiment`, `range`; values not defined. Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.8.1, UC-34, BR-62.

### GET /news/sentiment-summary
Status: PLANNED (spec only)
Auth: trader (PRO+ per `NEWS_AI_INSIGHT`)
Purpose: 24h sentiment summary.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.8.1.

## ai — SCR-29 (T-072 … T-076)

FREE can read existing conversations and sees an upgrade prompt; asking needs `AI_CHAT_DAILY` > 0
(PRO 30, PREMIUM 100 per day, reset 00:00 UTC+7); performance context PREMIUM only. Quota → 429
`AI_DAILY_QUOTA_EXHAUSTED` MSG30 (code exists). Failure → MSG31. Answer push planned on
`/user/queue/ai`.

### GET /ai/conversations
Status: PLANNED (spec only)
Auth: trader
Purpose: List conversations (UC-36).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.9.1.

### POST /ai/conversations
Status: PLANNED (spec only)
Auth: trader (PRO+)
Purpose: Start a conversation.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, UC-36.

### PATCH /ai/conversations/{id}
Status: PLANNED (spec only)
Auth: trader
Purpose: Rename a conversation.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, UC-36.

### DELETE /ai/conversations/{id}
Status: PLANNED (spec only)
Auth: trader
Purpose: Delete a conversation.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, UC-36.

### GET /ai/conversations/{id}/messages
Status: PLANNED (spec only)
Auth: trader
Purpose: Messages of a conversation.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, UC-35.

### POST /ai/conversations/{id}/messages
Status: PLANNED (spec only)
Auth: trader (PRO+, quota)
Purpose: Ask a question with a context selector (UC-35).
Request/Response: not defined. Errors: MSG29, MSG30 (429), MSG31.
FE notes: the answer is asynchronous (NSF-16); show a pending state. Disclaimer on every answer.
Source: none. Spec: TD 8, SRS 3.9.1, UC-35, BR-50…BR-52.

## billing — SCR-30 … SCR-32 (T-066 … T-071)

### GET /billing/packages
Status: PLANNED (spec only)
Auth: trader (the chain already lists it as TRADER)
Purpose: Packages for sale (UC-37). Prices (VND): PRO 99,000 / 30 d, 990,000 / 365 d; PREMIUM 199,000 / 30 d, 1,990,000 / 365 d.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.10, UC-37, D-58.

### POST /billing/orders
Status: PLANNED (spec only)
Auth: trader
Purpose: Create an order (NEW / RENEW / UPGRADE / DOWNGRADE) and get the gateway URL (UC-38).
Request: header `Idempotency-Key` (TD 8); body not defined. Errors: MSG47 for a refused upgrade.
Source: none. Spec: TD 8, SRS 3.10.1, UC-38, BR-53…BR-56.

### GET /billing/orders
Status: PLANNED (spec only)
Auth: trader
Purpose: Payment history (UC-39, SCR-32).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.10.2.

### GET /billing/orders/{code}
Status: PLANNED (spec only)
Auth: trader
Purpose: One order; SCR-31 polls it after the gateway return.
FE notes: take the result from the order status, **never** from the gateway's return parameters (T-071). MSG35 / MSG36 / MSG37.
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.10.2.

### GET /billing/subscription
Status: PLANNED (spec only)
Auth: trader
Purpose: Current plan, end date, scheduled subscriptions, usage of limits and today's AI quota (SCR-07 Subscription tab).
FE notes: this is the endpoint CR-08 locks would need (FEQ-02).
Request/Response/Errors: not defined.
Source: none. Spec: TD 8, SRS 3.2.5.

### POST /billing/ipn/vnpay
Status: PLANNED (spec only)
Auth: gateway signature (not FE)
Purpose: VNPay server-to-server callback. FE never calls it.
Source: none. Spec: TD 5.3, TD 8, NSF-12.

### POST /billing/ipn/momo
Status: PLANNED (spec only)
Auth: gateway signature (not FE)
Purpose: MoMo callback. FE never calls it.
Source: none. Spec: TD 5.3, TD 8, NSF-12.

### GET /billing/return/{gateway}
Status: PLANNED (spec only)
Auth: gateway signature
Purpose: Browser return from the gateway. `deploy/.env.example` points the return URLs at the web app (`http://localhost:5173/payment/result`); which of the two receives the browser is not decided.
Source: none. Spec: TD 5.3, TD 8.

## notification — SCR-15 (T-056, T-059)

### GET /notifications
Status: PLANNED (spec only)
Auth: trader
Purpose: Notification list, newest first, with unread count for the bell (UC-15).
Request/Response/Errors: not defined. Push planned on `/user/queue/notifications`.
FE notes: opening one marks it read and deep-links to the alert, plan, post or subscription.
Source: none. Spec: TD 8, TD 9, SRS 3.4.5, UC-15.

### POST /notifications/{id}/read
Status: PLANNED (spec only)
Auth: trader
Purpose: Mark one as read.
Source: none. Spec: TD 8.

### POST /notifications/read-all
Status: PLANNED (spec only)
Auth: trader
Purpose: Mark all as read.
Source: none. Spec: TD 8.

## admin — SCR-33 … SCR-44 (T-082 … T-087)

`/admin/**` is ADMIN-only in the chain already. TD 8 names areas, not methods:

| Area | Screen / UC | Task |
|---|---|---|
| `/admin/dashboard` | UC-40 | T-086 |
| `/admin/reports` | UC-41 (CSV export) | T-086 |
| `/admin/users` | UC-42 (lock, unlock, ban, role; MSG39) | T-083 |
| `/admin/reports-queue` | UC-43 moderation | T-084 |
| `/admin/pairs` | UC-45 (MSG40); `bracket-templates` below | T-085; PR #93 |
| `/admin/leverage-brackets` | UC-46 | T-085 |
| `/admin/packages` | UC-47 | T-066+ |
| `/admin/orders` | UC-48 | T-066+ |
| `/admin/news-sources` | UC-49 | T-077 |
| `/admin/ai-configurations` | UC-50 | T-071/T-073 |
| `/admin/settings` | UC-51 | T-082 |
| `/admin/audit-log` | UC-52, SCR-44 (search, CSV export) | T-115, PENDING PR #93 (below) |
| `/admin/system-events`, `/admin/system-health` | UC-52, SCR-44 (system log, API health) | T-115, PENDING PR #93 (below) |
| `/admin/announcements` | UC-44 | T-084 |

Status: PLANNED (spec only) in this file for the rows without a section below. The sections below are
PENDING PR (`feat/uc-52-audit-log`, PR #93, head `cedc28b`): build against them behind a flag. UC-52
is the SRS v1.0 number; the renumbered SRS calls it UC-46 (Q-82). Spec: TD 8, SRS 3.11.

### GET /admin/audit-log
Status: PENDING PR (`feat/uc-52-audit-log`, PR #93)
Auth: admin
Purpose: The audit log of SCR-44, newest first, read only (UC-52, D-130).

Query (all optional): `actor` (part of the actor's email or display name), `actorId` (uuid),
`actorType` (`USER`, `SYSTEM`), `action` (an `AuditAction`; repeat the parameter for several),
`entityType` (an `AuditedEntity`), `entityId` (uuid), `from`, `to` (`YYYY-MM-DD`, business days
UTC+7, `to` included), `page`, `pageSize` (20 by default; paging as `03-conventions.md`).

Response `200`: a page of

```ts
interface AuditLogEntry {
  id: string;
  recordedAt: string;                 // ISO instant
  actor: {                            // null when the system acted
    id: string;
    email: string | null;             // null when the account no longer exists
    displayName: string | null;
    role: 'TRADER' | 'ADMIN' | null;
  } | null;
  action: string;                     // AuditAction
  entityType: string | null;          // AuditedEntity
  entityId: string | null;            // null for a system setting or an export
  ipAddress: string | null;
  oldValue: unknown | null;           // changed fields before, secrets redacted
  newValue: unknown | null;
}
```

Header `X-Result-Truncated: actor`: the actor text matched more than 500 accounts and only the
newest 500 were searched. Show a hint to narrow the actor text.

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Unknown filter value (enum, uuid, date); a NUL byte in `actor` (D-132) |
| 400 | `VALIDATION_FAILED` | MSG15 | Period, `page` or `pageSize` not accepted |

Source: `backend/src/main/java/com/cryptopilot/admin/controller/AuditLogController.java#L60`;
`admin/dto/response/AuditLogEntryResponse.java`. Spec: SRS 3.11.9, BR-57, D-130.

### GET /admin/audit-log/export
Status: PENDING PR (`feat/uc-52-audit-log`, PR #93)
Auth: admin
Purpose: The same search as a CSV file (UC-52).

Query: the filters of `GET /admin/audit-log`, no paging. Response `200` `text/csv`, attachment
`cryptopilot-audit-log[-{from}][-{to}].csv`, a header line then one line per entry, at most 10,000
entries. When more matched: `X-Total-Count: <n>` and `X-Result-Truncated: export` (`actor,export`
when the actor text was cut too). Both headers are exposed through CORS. Every export is itself an
audit entry (`AUDIT_LOG_EXPORTED`, entity `AUDIT_LOG`). Errors: as the search, without paging.

Source: `backend/src/main/java/com/cryptopilot/admin/controller/AuditLogController.java#L96`. Spec: SRS 3.11.9, D-130.

### GET /admin/system-events
Status: PENDING PR (`feat/uc-52-audit-log`, PR #93)
Auth: admin
Purpose: The system log of SCR-44: unexpected errors, failed jobs and failed external calls, the
latest seen first (UC-52, D-130).

Query (all optional): `category` (`SystemEventCategory`), `source` (`SystemEventSource`), `from`,
`to` (days on which the failure was last seen), `page`, `pageSize` (20 by default).

Response `200`: a page of

```ts
interface SystemEvent {
  id: string;
  category: 'SYSTEM_ERROR' | 'EXTERNAL_API_FAILURE';
  source: string;            // SystemEventSource
  operation: string;         // e.g. "GET /api/v1/plans/{planId}", a job or a client method
  errorType: string;         // class of what was thrown
  message: string | null;
  reference: string | null;  // the reference a 500 answered with; match it to a user's report
  occurrences: number;       // repeats merged into this row (same failure, 10-minute bucket)
  firstSeenAt: string;
  lastSeenAt: string;
}
```

Rows are kept 90 days. An external 4xx is not listed (the service answered), except 401, 403, 408,
418 and 429. Errors: 400 MSG01 (unknown filter value), MSG15 (period, `page`, `pageSize`).

Source: `backend/src/main/java/com/cryptopilot/admin/controller/SystemMonitorController.java#L42`;
`admin/dto/response/SystemEventResponse.java`. Spec: UC-52, D-130.

### GET /admin/system-health
Status: PENDING PR (`feat/uc-52-audit-log`, PR #93)
Auth: admin
Purpose: The health panel of SCR-44: each external service and each market's data feed (D-130).

Response `200`, read on each call:

```ts
interface SystemHealth {
  checkedAt: string;
  recentWindowMinutes: number;   // 15: a failure this recent makes a service DOWN or DEGRADED
  staleAfterMinutes: number;     // 5: a feed whose latest candle is older is stale
  services: Array<{
    source: 'BINANCE_REST' | 'AI_SERVICE' | 'MEDIA_STORAGE' | 'NEWS_SOURCE' | 'MAIL';
    status: 'UP' | 'DEGRADED' | 'DOWN' | 'UNKNOWN';
    lastSuccessAt: string | null;  // since the backend started
    lastFailureAt: string | null;
    failures24h: number;
    lastError: string | null;
    bannedUntil: string | null;    // Binance only: end of an IP ban
  }>;
  feeds: Array<{
    market: 'SPOT' | 'FUTURES';
    latestCandleAt: string | null;
    lagSeconds: number | null;
    stale: boolean;               // true also when nothing is stored
  }>;
}
```

Source: `backend/src/main/java/com/cryptopilot/admin/controller/SystemMonitorController.java#L59`;
`admin/dto/response/SystemHealthResponse.java`. Spec: UC-52, D-130.

### GET /admin/pairs/bracket-templates
Status: PENDING PR (`feat/uc-52-audit-log`, PR #93)
Auth: admin
Purpose: Ready-made leverage brackets SCR-38 can start from (D-131).

Response `200`: `[{ id: 'MAJOR' | 'ALTCOIN' | 'SMALL_CAP', firstLeverage: number, brackets:
[{ bracketNo, notionalFloor, notionalCap, maxLeverage, maintenanceMarginRate, maintenanceAmount }] }]`
(decimals as strings). `firstLeverage` is the template's highest leverage: a pair whose
`maxLeverage` is above it cannot use it (BR-26). The maintenance amounts are computed by BR-27; save
the rows with `PUT /admin/pairs/{id}/brackets` as usual.

Related changes to `PUT /admin/pairs/{id}` on the same PR: `status: INACTIVE` stores both market
switches off and `maxLeverage: null` whatever the body says (re-activating offers no market until
one is switched on); switching Futures on for a pair with no brackets stores a default template
(MAJOR for BTC and ETH, ALTCOIN otherwise); a fractional `maxLeverage` is 400 MSG01 (D-132). A
market switched on starts streaming within seconds of the answer, not after up to 5 minutes.

Source: `backend/src/main/java/com/cryptopilot/market/controller/PairAdminController.java#L71`;
`market/dto/response/BracketTemplateResponse.java`; `market/model/enums/BracketTemplate.java`.
Spec: SRS 3.11.4, BR-26, BR-27, D-131.
