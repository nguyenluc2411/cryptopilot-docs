# Module: watchlist (watchlist + alerts)

Screens SCR-12 (watchlist), SCR-13 (alert list), SCR-14 (alert dialog).
All endpoints: TRADER only. Code prefix: `backend/src/main/java/com/cryptopilot/watchlist/`.

- Watchlist: IMPLEMENTED on `develop` (T-053, D-75).
- Alerts: **PENDING PR** on `feat/t-054-alert-rules` @ `0803903` (T-054, D-76). Not callable on
  `develop`. The same branch changes `DELETE /watchlist/{id}`.
- Alert evaluation (NSF-06, T-055) and notifications (T-056) do not exist: alerts never fire yet, so
  `triggerCount` stays 0 and `TRIGGERED`/`EXPIRED` are never set.

Shared type:

```ts
interface WatchlistItem {
  id: string;            // watchlist row id
  pairId: string;
  symbol: string;
  spotListed: boolean;   // enabled on Spot now
  futuresListed: boolean;
  label: string | null;
  note: string | null;
  sortOrder: number;
  activeAlerts: number;  // ACTIVE alerts of this row
  addedAt: string;
}
```

---

### GET /watchlist
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: The caller's whole watchlist with the plan's limit (SCR-12, UC-12).

Response `200`:

```json
{
  "items": [
    {
      "id": "0199a1b2-7c3d-7e4f-8a9b-0c1d2e3f4a5b",
      "pairId": "0199a0f0-1111-7aaa-8bbb-000000000001",
      "symbol": "BTCUSDT",
      "spotListed": true,
      "futuresListed": true,
      "label": "Majors",
      "note": null,
      "sortOrder": 0,
      "activeAlerts": 2,
      "addedAt": "2026-10-01T03:12:44Z"
    }
  ],
  "limit": 5
}
```

```ts
interface WatchlistResponse { items: WatchlistItem[]; limit: number | null } // null = unlimited
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 401 | `AUTHENTICATION_REQUIRED` | MSG44 | No session |

FE notes:
- Not paged; ordered by `sortOrder`, then `addedAt`. Group by `label` on the client (SRS 3.4.1).
- Last price, 24h change and 1h setup score are **not** in the row (D-75): take prices from
  `/topic/overview.SPOT` and the score from `GET /analysis/spot/{symbol}?tf=1h` per row (or skip
  the score until a batch read exists).
- A row whose `spotListed` and `futuresListed` are both false is a pair an admin disabled. Keep it
  visible, greyed, removable; it still counts toward the limit (Q-29, closed).
- `limit` is the only plan hint the API gives today; show "n / limit".
Source: `watchlist/controller/WatchlistController.java#L54`; `watchlist/dto/response/WatchlistResponse.java#L14`; `watchlist/dto/response/WatchlistItemResponse.java#L23`. Spec: SRS 3.4.1, UC-12, BR-15, D-75, Q-29.

---

### POST /watchlist
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Add a pair at the end of the list.

| Field | Type | Required | Rule |
|---|---|---|---|
| `pairId` | UUID | yes | not null → MSG01; must be enabled on at least one market → 404 |
| `label` | string | no | ≤ 100 → MSG01; blank = none |
| `note` | string | no | ≤ 1000 → MSG01; blank = none |

Response `201`: the new `WatchlistItem` (`activeAlerts: 0`).

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Field rules | Under field |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Unknown pair or not enabled anywhere | Inline |
| 409 | `WATCHLIST_PAIR_ALREADY_WATCHED` | MSG45 | Already watched; `messageArgs[0]` = symbol | Inline |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | `WATCHLIST_MAX`; args `[max, "watchlist items", tier]` | Inline + upgrade |

FE notes: on 201 show MSG25 with `symbol`. Optimistic insert is fine; roll back on error.
**Pair id:** take `pairId` from `GET /market/pairs` (FEQ-01, M-01; backend `fix/feq-01-pair-id` `5ef54e1`, not yet on `develop`).
Source: `watchlist/controller/WatchlistController.java#L65`; `watchlist/dto/request/AddWatchlistItemRequest.java#L16`. Spec: SRS 3.4.1, BR-15, BR-62, D-63, D-75.

---

### PATCH /watchlist/{id}
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Change label, note or position of one row.

| Field | Type | Required | Rule |
|---|---|---|---|
| `label` | string | no | ≤ 100 → MSG01. `null`/absent = unchanged; `""` = clear |
| `note` | string | no | ≤ 1000 → MSG01. `null`/absent = unchanged; `""` = clear |
| `sortOrder` | int | no | ≥ 0 → MSG01. `null`/absent = unchanged |

Response `200`: the updated `WatchlistItem`.

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Field rules |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's row |

FE notes: `sortOrder` sets **only this row**; the server does not renumber the others. After a drag,
PATCH every row whose position changed (e.g. renumber 0…n−1) and refetch the list. Equal values are
allowed; ties fall back to `addedAt`.
Source: `watchlist/controller/WatchlistController.java#L77`; `watchlist/dto/request/UpdateWatchlistItemRequest.java#L16`; `watchlist/entity/Watchlist.java#L77`. Spec: SRS 3.4.1, D-75.

---

### DELETE /watchlist/{id}
Status: IMPLEMENTED (develop) — `expectedAlertCount` is PENDING PR (`feat/t-054-alert-rules`)
Auth: trader
Purpose: Remove a row and all its alerts (BR-16).

| Query | Type | Required | Rule |
|---|---|---|---|
| `confirm` | boolean | no | default `false`; must be `true` when the row has alerts |
| `expectedAlertCount` | int | no | **branch only.** The `{n}` the user confirmed in MSG26 |

Response `204`.

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `WATCHLIST_REMOVAL_CONFIRMATION_REQUIRED` | MSG26 | Row has alerts and `confirm` is not true; (branch) or `expectedAlertCount` ≠ current count. `messageArgs` = `[symbol, n]` | MSG26 dialog with the new `n` |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's row | Remove from cache |

FE notes (T-059 gotcha):
1. If `activeAlerts` > 0 (or on a 400 MSG26), show MSG26 with `messageArgs`.
2. On "Continue", send `DELETE /watchlist/{id}?confirm=true&expectedAlertCount={n}` with the `n`
   shown. If alerts were added meanwhile, the server answers MSG26 again with the new `n` and
   removes nothing — show the dialog again.
3. `activeAlerts` counts ACTIVE alerts only; MSG26's `n` counts **all** alerts of the row (paused,
   triggered, expired too). Use the server's `n`.
4. On `develop` (before T-054 merges) `expectedAlertCount` is ignored; sending it is harmless.
Source: `watchlist/controller/WatchlistController.java#L92` (develop), `#L94` (branch); `watchlist/service/impl/WatchlistServiceImpl.java#L120`. Spec: SRS 3.4.1, BR-16, D-76.

---

## Alerts — PENDING PR (`feat/t-054-alert-rules`)

Shared types (branch):

```ts
type AlertType = 'PRICE' | 'INDICATOR';
type AlertIndicator = 'RSI_14' | 'MACD_CROSS' | 'EMA_CROSS' | 'FUNDING_RATE' | 'OPEN_INTEREST_CHANGE';
type ConditionOperator = 'CROSS_ABOVE' | 'CROSS_BELOW' | 'GREATER_THAN' | 'LESS_THAN';
type TriggerMode = 'ONCE' | 'ONCE_PER_BAR' | 'EVERY_TIME';
type AlertStatus = 'ACTIVE' | 'PAUSED' | 'TRIGGERED' | 'EXPIRED';

interface AlertRuleBody {
  market: 'SPOT' | 'FUTURES';
  type: AlertType;
  indicator?: AlertIndicator | null;
  timeframe?: '15m' | '1h' | '4h' | '1d' | null;
  condition: ConditionOperator;
  threshold?: string | null;
  triggerMode: TriggerMode;
  cooldownMinutes?: number | null;
  notifyEmail?: boolean;          // default false
  notifyPush?: boolean;           // default false
  expiresAt?: string | null;      // ISO instant, (now, now + 90 d]
}
interface CreateAlertRequest extends AlertRuleBody { pairId: string }

interface AlertResponse {
  id: string;
  watchlistId: string;
  pairId: string;
  symbol: string;
  market: 'SPOT' | 'FUTURES';
  type: AlertType;
  indicator: AlertIndicator | null;
  timeframe: string | null;       // "1h" for FUNDING_RATE / OPEN_INTEREST_CHANGE (server-set)
  condition: ConditionOperator;
  threshold: string | null;       // PRICE: rounded to the tick
  triggerMode: TriggerMode;
  cooldownMinutes: number | null;
  notifyInApp: boolean;           // always true
  notifyEmail: boolean;
  notifyPush: boolean;
  status: AlertStatus;
  triggerCount: number;
  lastTriggeredAt: string | null;
  expiresAt: string | null;
  createdAt: string;
}
```

Rule validation (server, 400 with `errors`; MSG01 = required or not applicable, MSG15 = out of range):

| Case | `indicator` | `timeframe` | `threshold` | `condition` | `market` |
|---|---|---|---|---|---|
| `PRICE` | absent | absent | required, > 0; rounded to tick (rounds to 0 → MSG15) | any | any |
| `RSI_14` | required | required | required, 0–100 | any | any |
| `MACD_CROSS`, `EMA_CROSS` | required | required | **absent** | `CROSS_ABOVE`/`CROSS_BELOW` | any |
| `FUNDING_RATE`, `OPEN_INTEREST_CHANGE` | required | **absent** (server uses 1h) | required, any sign | any | `FUTURES` |

Plus: `EVERY_TIME` needs `cooldownMinutes` (≥ 1); `cooldownMinutes` < 1 → MSG15; `expiresAt` must be
after now and within 90 days → MSG15 `errors.expiresAt`. Threshold ≤ 16 integer / 12 decimal digits.

Check order on create/edit/resume: field rules (400) → plan features (403 MSG29) → pair enabled on
the market (404 MSG41) → limits under the per-user lock (409 MSG27).

Plan features: `INDICATOR` → `INDICATOR_ALERT`; `FUTURES` market → `FUTURES_ANALYSIS`;
`notifyEmail`/`notifyPush` true → `EXTERNAL_ALERT_CHANNELS`. All three are PRO+.

Source (branch): `watchlist/service/impl/AlertRuleValidator.java#L44`; `watchlist/dto/request/CreateAlertRequest.java#L23`; `watchlist/dto/request/UpdateAlertRequest.java#L22`; `watchlist/dto/response/AlertResponse.java#L39`. Spec: SRS 3.4.2, BR-17…BR-20, A-40, D-76.

---

### GET /alerts
Status: PENDING PR (feat/t-054-alert-rules)
Auth: trader
Purpose: The caller's alerts, newest first (SCR-13, UC-14).

| Query | Type | Required | Rule |
|---|---|---|---|
| `status` | `AlertStatus` | no | upper case; all when absent |
| `type` | `AlertType` | no | upper case; both when absent |
| `page` | int | no | ≥ 1 → MSG15 `errors.page` |
| `pageSize` | int | no | 1–100, default 20 → MSG15 `errors.pageSize` |

Response `200`: `PageResponse<AlertResponse>`.

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/MSG15 | Bad enum or paging |

FE notes: no `GET /alerts/{id}`; the list row carries every field. Filter by pair on the client.
Trigger history (SRS 3.4.3) comes with notifications (T-056/T-059). Q-31: no "paused by plan change"
marker yet.
Source (branch): `watchlist/controller/AlertController.java#L55`. Spec: SRS 3.4.3, CR-04, D-76.

---

### POST /alerts
Status: PENDING PR (feat/t-054-alert-rules)
Auth: trader (+ plan features above)
Purpose: Create an ACTIVE alert; adds the pair to the watchlist if needed (BR-16).

Request: `CreateAlertRequest` (table above).

```json
{
  "pairId": "0199a0f0-1111-7aaa-8bbb-000000000001",
  "market": "SPOT",
  "type": "PRICE",
  "condition": "CROSS_ABOVE",
  "threshold": "65000",
  "triggerMode": "ONCE",
  "notifyEmail": false,
  "notifyPush": false,
  "expiresAt": "2026-11-01T00:00:00Z"
}
```

Response `201`: `AlertResponse` with `status: "ACTIVE"`.

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/MSG15 | Rule table | Under each field |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | Indicator / Futures / email-push on FREE | MSG29 dialog |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Pair not enabled on that market | Inline |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | `ACTIVE_ALERT_MAX`, or `WATCHLIST_MAX` when the pair had to be added | Inline + upgrade |

FE notes: show MSG14 on success. Invalidate `GET /watchlist` too (a row may be new, `activeAlerts`
changed). On FREE show INDICATOR, Futures and channel switches with a lock (CR-08) instead of hiding
them. FUNDING_RATE threshold unit is undecided (Q-30) — do not ship that input before it is answered.
Source (branch): `watchlist/controller/AlertController.java#L77`. Spec: SRS 3.4.2, UC-13, BR-16, BR-17, BR-62.

---

### PUT /alerts/{id}
Status: PENDING PR (feat/t-054-alert-rules)
Auth: trader (+ plan features)
Purpose: Edit an alert; the pair cannot change. A TRIGGERED or EXPIRED alert becomes ACTIVE.

Request: `AlertRuleBody` (no `pairId`). Full replacement of the rule.

Response `200`: `AlertResponse`.

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/MSG15 | Rule table |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | Feature not in plan |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's, or pair not enabled on the market |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | Re-activation would pass `ACTIVE_ALERT_MAX` |

FE notes: show MSG14. Editing a PAUSED alert keeps it PAUSED.
Source (branch): `watchlist/controller/AlertController.java#L92`. Spec: SRS 3.4.2, 3.4.3, D-76.

---

### DELETE /alerts/{id}
Status: PENDING PR (feat/t-054-alert-rules)
Auth: trader
Purpose: Delete an alert (after a client-side confirmation).

Response `204`.

| Status | `code` | MSG | When |
|---|---|---|---|
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's |

Source (branch): `watchlist/controller/AlertController.java#L104`. Spec: SRS 3.4.3.

---

### POST /alerts/{id}/pause
Status: PENDING PR (feat/t-054-alert-rules)
Auth: trader
Purpose: ACTIVE → PAUSED.

Response `200`: `AlertResponse` with `status: "PAUSED"`.

| Status | `code` | MSG | When |
|---|---|---|---|
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's |
| 409 | `ALERT_STATUS_TRANSITION_INVALID` | MSG43 | Not ACTIVE |

Source (branch): `watchlist/controller/AlertController.java#L115`. Spec: SRS 3.4.3.

---

### POST /alerts/{id}/resume
Status: PENDING PR (feat/t-054-alert-rules)
Auth: trader (+ plan features of the alert)
Purpose: PAUSED → ACTIVE, subject to the current plan's limits.

Response `200`: `AlertResponse` with `status: "ACTIVE"`.

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG15 | `expiresAt` has passed (`errors.expiresAt`) | "Edit it instead" |
| 403 | `PLAN_FEATURE_NOT_INCLUDED` | MSG29 | Its type/market is no longer in the plan | MSG29 |
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not the caller's, or pair disabled | Inline |
| 409 | `PLAN_LIMIT_REACHED` | MSG27 | `ACTIVE_ALERT_MAX` | Inline |
| 409 | `ALERT_STATUS_TRANSITION_INVALID` | MSG43 | Not PAUSED | Reload |

Source (branch): `watchlist/controller/AlertController.java#L129`. Spec: SRS 3.4.3, BR-17, BR-64.
