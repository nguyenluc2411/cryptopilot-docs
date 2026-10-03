# 03 · Conventions

## JSON

| Rule | Detail |
|---|---|
| Field names | camelCase, exactly as the Java record components |
| Decimals (`BigDecimal`) | **Strings**, plain notation, e.g. `"63000.5"`, `"0.00010000"`. Never parse into `number` for money, price or quantity; use a decimal library (`decimal.js`, `big.js`; Dart `decimal`) |
| Integers | JSON numbers (`displayOrder`, `score`, `leverage`, `triggerCount`, `activeAlerts`, `total`) |
| Instants | ISO 8601 UTC strings with `Z`, e.g. `"2026-09-21T10:15:00Z"` |
| UUIDs | Strings (UUID v7) |
| Enums | Upper-case names, e.g. `"SPOT"`, `"DRAFT"`. See `04-enums.md` |
| Null | A field with no value is present with `null` in REST bodies (e.g. analysis values not computable yet). Treat missing and `null` the same way |
| Request decimals | Send as strings (`"0.5"`) or numbers; both parse. Strings keep precision, so prefer them |
| Request enums | Upper case in JSON bodies (Jackson enum names are case-sensitive) |

Source: `backend/src/main/java/com/cryptopilot/common/config/JacksonConfig.java#L39`. Spec: TD 5.4, TD 8.

## Dates and time zone

- The API speaks UTC only. Display in UTC+7 as `dd/MM/yyyy HH:mm` (CR-01).
- Candle boundaries are UTC (BR-08). A 1d candle opens at 00:00 UTC = 07:00 UTC+7.
- "Daily" limits (AI quota, verification resend) reset at 00:00 UTC+7 (A-21, D-57).
- Query parameters `from`/`to` are ISO 8601 instants: `2026-10-01T00:00:00Z`. Percent-encode `+`
  if you use an offset; `Z` avoids it.

## Display precision (CR-02, CR-03)

| Value | Display |
|---|---|
| Price | Precision of the pair's `tickSize` (from `GET /market/pairs`) |
| Quantity | Precision of `stepSize` |
| USDT amount | 2 decimals |
| VND amount | 0 decimals |
| Percent | 2 decimals |
| Rounding for display | Half-up. Never round before sending: the server rounds prices to the tick (half-up) and floors quantities to the step |

Funding rate is a fraction (`"0.0001"` = 0.01 %); multiply by 100 to show a percent. Market
`changePercent24h` is already a percent.

## Pagination

Request: `?page=1&pageSize=20`. `page` starts at **1**. `pageSize` 1–100, default 20 (CR-04).

```ts
interface PageResponse<T> {
  items: T[];
  page: number;      // as requested
  pageSize: number;  // as requested
  total: number;     // all matching rows
}
```

Last page: `page * pageSize >= total`. A page past the end returns `items: []` with the real
`total`. Invalid `page`/`pageSize` → 400 MSG01 (market) or MSG15 with `errors.page` /
`errors.pageSize` (plans, alerts).

Endpoints that are **not** paged: `GET /watchlist` (whole list, max 100), `GET /market/{market}/{symbol}/candles`
(`limit`), `GET /market/futures/{symbol}/metrics` (range).

Sorting: there is no `sort` parameter anywhere. Each list has a fixed order, written per endpoint
(plans and alerts newest first; pairs by admin display order then symbol; watchlist by `sortOrder`
then `addedAt`).

Source: `backend/src/main/java/com/cryptopilot/common/web/PageResponse.java#L24`. Spec: TD 8, CR-04.

## Success bodies

- Reads return the resource.
- Some writes return only a message code to display:

```ts
interface MessageResponse { messageCode: string }  // e.g. { "messageCode": "MSG14" }
```

- `204 No Content` has no body (logout, delete).

Source: `backend/src/main/java/com/cryptopilot/common/web/MessageResponse.java#L19`.

## Error shape (RFC 9457 problem detail)

Every error, including 401/403 from the security chain, has this body with
`Content-Type: application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "FREE allows 5 watchlist items and 5 are held",
  "instance": "/api/v1/watchlist",
  "code": "PLAN_LIMIT_REACHED",
  "messageCode": "MSG27",
  "traceId": "0199a1b2-7c3d-7e4f-8a9b-0c1d2e3f4a5b",
  "messageArgs": ["5", "watchlist items", "FREE"]
}
```

```ts
interface ApiProblem {
  type?: string;             // "about:blank" when present
  title: string;             // HTTP reason phrase
  status: number;
  detail: string;            // English, for logs and developers. Never show it to users
  instance?: string;         // request path
  code: ErrorCode;           // stable; branch on this
  messageCode: string;       // "MSG01".."MSG48"; the text to show (table below)
  traceId?: string;          // show as the reference in MSG43, send in bug reports
  messageArgs?: string[];    // values for the {placeholders} of the message, in order
  errors?: Record<string, string>; // field -> "MSG01" | "MSG15" | ..., or a parser note
}
```

How to display (CR-05, CR-07):

1. If `errors` is present, show each value under its field. The value is a **message code**
   (`"MSG15"`) from bean validation and business checks, or a short English note (`"is required"`,
   `"is invalid"`, `"is not readable"`) from request binding — map the notes to MSG01.
2. Otherwise show the message of `messageCode`, filling placeholders from `messageArgs`.
3. MSG43 always carries the reference: show `traceId` as `{code}`.
4. Field errors carry **no** arguments. MSG15 (`{field} must be between {min} and {max}`) and MSG16
   (`For {direction} positions: {rule}`) must be completed by the client from its own field labels
   and limits.

Field error keys that are not field names:

| Key | Endpoint | Meaning |
|---|---|---|
| `confirmPasswordMatching` | register, reset-password, change password | Password and confirmation differ (MSG03, A-20). Show under the confirm field |
| `acceptsDisclaimer` | register | Disclaimer not accepted (MSG01) |
| `body` | any | Body is not readable JSON |
| `quantity`, `notional` | plans | The risk budget buys less than one step, or the notional is below the pair minimum / above the top bracket (MSG15). Show in the risk panel, not under an input |
| `page`, `pageSize` | plans, alerts | MSG15 |

Some MSG01 responses carry **no** `errors` (market endpoints: a bad `market`, `tf`, `limit`, range or
`page`). Show MSG01 as a banner then.

Source: `backend/src/main/java/com/cryptopilot/common/exception/GlobalExceptionHandler.java#L87`,
`backend/src/main/java/com/cryptopilot/common/exception/ProblemDetails.java#L49`,
`backend/src/main/java/com/cryptopilot/auth/config/SecurityProblemDetailHandler.java`.
Spec: TD 5.1, D-25, RFC 9457.

## Error codes (`ErrorCode`, develop)

| `code` | Status | MSG | When | FE action |
|---|---|---|---|---|
| `VALIDATION_FAILED` | 400 | MSG01 | Body/parameter invalid; `errors` usually present | Field errors, else banner |
| `RESOURCE_NOT_FOUND` | 404 | MSG41 | Unknown id, another user's row, pair not enabled | "No results found." Drop stale cache entry |
| `INTERNAL_ERROR` | 500 | MSG43 | Unexpected | Toast with `traceId` |
| `INVALID_CREDENTIALS` | 401 | MSG08 | Login: wrong email or password | Inline on SCR-04. **Not** a session end |
| `LOGIN_TEMPORARILY_LOCKED` | 429 | MSG09 | 5 failed logins; `messageArgs[0]` = minutes left | Inline, disable submit |
| `ACCOUNT_NOT_ACTIVE` | 403 | MSG10 | Login of a LOCKED/BANNED account; `messageArgs[0]` = `LOCKED`/`BANNED` | Inline |
| `SESSION_EXPIRED` | 401 | MSG44 | Refresh token reused, expired or revoked | Drop tokens, MSG44 dialog, SCR-04 |
| `EMAIL_NOT_VERIFIED` | 403 | MSG11 | Login before verification | Inline with "Resend" link |
| `EMAIL_ALREADY_VERIFIED` | 409 | MSG07 | Verify a link of an already verified account | Show MSG07, offer login |
| `ACCOUNT_STATUS_TRANSITION_INVALID` | 409 | MSG39 | Admin status change refused (planned T-083) | — |
| `TOKEN_INVALID_OR_EXPIRED` | 400 | MSG07 | Verify/reset link invalid, used or expired | MSG07 with "Resend" |
| `EMAIL_ALREADY_REGISTERED` | 409 | MSG04 | Register with a known email | Under the email field |
| `PASSWORD_POLICY_VIOLATION` | 400 | MSG03 | Password breaks BR-02 (service-side check) | Under the password field |
| `DATA_CONFLICT` | 409 | MSG43 | Lost race on a unique key or optimistic lock | Reload the resource, let the user retry; show `traceId` |
| `CURRENT_PASSWORD_INCORRECT` | 400 | MSG08 | Change password: wrong current password | Under current password. **Do not** sign out (D-35) |
| `AUTHENTICATION_REQUIRED` | 401 | MSG44 | No/invalid/expired access token, or session revoked | Refresh once, then MSG44 dialog |
| `ACCESS_DENIED` | 403 | MSG43 | Role not allowed (A-24) | Route away; it is a client bug |
| `PLAN_FEATURE_NOT_INCLUDED` | 403 | MSG29 | Feature not in plan; `messageArgs[0]` = lowest tier | MSG29 dialog with "View plans" |
| `PLAN_LIMIT_REACHED` | 409 | MSG27 | Limit; `messageArgs` = `[max, items, tier]` | Inline MSG27 with upgrade link |
| `AI_DAILY_QUOTA_EXHAUSTED` | 429 | MSG30 | (planned AI) `messageArgs[0]` = quota | Inline |
| `RISK_PROFILE_CONFIRMATION_REQUIRED` | 400 | MSG48 | AGGRESSIVE chosen without confirmation | Show MSG48 dialog, resend with `confirmAggressive: true` |
| `TRADING_BLOCKING_WARNING` | 409 | MSG18 | Activate a plan with a BLOCKING warning | Error banner |
| `TRADING_PLAN_STATUS_TRANSITION_INVALID` | 409 | MSG43 | Edit/activate/cancel in the wrong status (A-38) | Reload plan; it changed elsewhere |
| `MARKET_PRICE_UNAVAILABLE` | 503 | MSG43 | MARKET plan with no live last price (A-39) | "Price unavailable, try again", keep form |
| `WATCHLIST_PAIR_ALREADY_WATCHED` | 409 | MSG45 | Pair already watched; `messageArgs[0]` = symbol | Inline |
| `WATCHLIST_REMOVAL_CONFIRMATION_REQUIRED` | 400 | MSG26 | Remove a watched pair that has alerts; `messageArgs` = `[symbol, n]` | MSG26 confirm dialog, resend with `confirm=true` |
| `ALERT_STATUS_TRANSITION_INVALID` | 409 | MSG43 | **PENDING PR (T-054).** Pause a non-ACTIVE / resume a non-PAUSED alert | Reload alert |

Source: `backend/src/main/java/com/cryptopilot/common/exception/ErrorCode.java#L23`
(`ALERT_STATUS_TRANSITION_INVALID` at `#L266` on `feat/t-054-alert-rules`).

## Message texts (SRS 5.3)

The backend sends codes; the client owns the text (D-25). `{…}` are filled from `messageArgs` in
order, or by the client where noted.

| Code | Type | Text |
|---|---|---|
| MSG01 | Under field | The {field} field is required. *(client fills {field})* |
| MSG02 | Under field | Please enter a valid email address. |
| MSG03 | Under field | Password must be 8-64 characters and include uppercase, lowercase letters and a digit. |
| MSG04 | Under field | This email is already registered. |
| MSG05 | Toast | Account created. Please check {email} to verify your account. *(client fills {email})* |
| MSG06 | Inline | Your email has been verified. You can now log in. |
| MSG07 | Inline | This link is invalid or has expired. |
| MSG08 | Inline | Incorrect email or password. Please check again. |
| MSG09 | Inline | Too many failed attempts. Please try again after {minutes} minutes. |
| MSG10 | Inline | Your account has been {status}. Please contact support. |
| MSG11 | Inline | Please verify your email before logging in. Resend verification email? |
| MSG12 | Toast | If the email is registered, a reset link has been sent. |
| MSG13 | Toast | Your password has been changed. Please log in again. |
| MSG14 | Toast | Saved successfully. |
| MSG15 | Under field | {field} must be between {min} and {max}. *(client fills)* |
| MSG16 | Under field | For {direction} positions: {rule}. *(client fills)* |
| MSG17 | Warning panel | {severity}: {warning message} *(from `warnings[]`)* |
| MSG18 | Error banner | This plan has blocking warnings and cannot be activated. |
| MSG19 | Toast | Trading plan activated. |
| MSG20 | Confirm dialog | Cancel this trading plan? This action cannot be undone. |
| MSG21 | Confirm dialog | Close this position at about {price}? Estimated P/L: {pnl}. *(planned)* |
| MSG22 | Notification | {pair} {direction} entry filled at {price}. *(planned)* |
| MSG23 | Notification | {pair} position closed by {reason} at {price}. P/L: {pnl}. *(planned)* |
| MSG24 | Notification | {pair} position was liquidated at {price}. Loss: {pnl}. *(planned)* |
| MSG25 | Toast | {pair} added to watchlist. *(client fills from the response `symbol`)* |
| MSG26 | Confirm dialog | Removing {pair} will also delete {n} alerts. Continue? |
| MSG27 | Inline | You have reached the limit of {max} {items} of the {plan} plan. Upgrade to increase the limit? |
| MSG28 | Notification | {pair}: {condition} ({value}). *(planned)* |
| MSG29 | Dialog | This feature is available on the {plan} plan or higher. View plans? |
| MSG30 | Inline | You have used today's {quota} questions. Quota resets at 00:00. *(planned)* |
| MSG31 | Inline | The AI Assistant is temporarily unavailable. Please try again. *(planned)* |
| MSG32 | Under field | File type or size is not supported (maximum {size}). *(planned)* |
| MSG33 | Toast | Your post has been published. *(planned)* |
| MSG34 | Toast | Thank you, your report has been submitted. / You have already reported this post. *(planned)* |
| MSG35 | Inline | Payment successful. Your {plan} subscription is active from {start} until {end}. *(planned)* |
| MSG36 | Inline | Payment was not completed. No amount has been charged by CryptoPilot. *(planned)* |
| MSG37 | Inline | We are confirming your payment with {gateway}. Please wait... *(planned)* |
| MSG38 | Notification, email | Your subscription expires on {date}. *(planned)* |
| MSG39 | Confirm dialog | {action} account {email}? Reason is required. *(planned)* |
| MSG40 | Inline | {pair} has open simulated positions and cannot be disabled. *(planned)* |
| MSG41 | Inline | No results found. |
| MSG42 | Footer / banner | Information on CryptoPilot is for reference and education only and is not investment advice. |
| MSG43 | Toast | Something went wrong. Please try again. (Ref: {code}) *(fill {code} with `traceId`)* |
| MSG44 | Dialog | Your session has expired. Please log in again. |
| MSG45 | Inline | {pair} is already in your watchlist. |
| MSG46 | Inline | Please wait {time} before requesting another verification email. *(not returned yet, T-105)* |
| MSG47 | Inline | The remaining value of your current subscriptions ({credit}) covers this package. Please choose a longer package. *(planned)* |
| MSG48 | Confirm dialog | The Aggressive profile allows higher risk per trade and higher leverage and can lead to large losses. Continue? |
| MSG49 | Notification | Your plan is now {plan}. {n} alerts have been paused because of the plan limits. *(planned)* |

`messageArgs` order per code (develop): MSG09 `[minutes]`; MSG10 `[status]`; MSG26 `[symbol, n]`;
MSG27 `[max, items, tier]`; MSG29 `[tier]`; MSG30 `[quota]`; MSG45 `[symbol]`. `items` is an English
phrase (`"active plans and open positions"`, `"watchlist items"`, `"active alerts"`); translate it on
the client if the UI is not English.

## Idempotency and concurrency

- No endpoint accepts an `Idempotency-Key` yet (planned for `POST /billing/orders`, TD 8).
- Writes are not idempotent: do not auto-retry a failed `POST`. Retry `GET` freely.
- Optimistic locking: a write that lost a race answers 409 `DATA_CONFLICT`. Reload and let the user
  decide again.
- Disable submit buttons while a write is in flight; this prevents most duplicates (e.g. two
  "Activate" clicks → the second answers 409 MSG43).

## Rate limits

TD 5.3 lists Bucket4j limits (login 10/min/IP, API 120/min/user, AI 10/min/user). **Not in code.** The
only 429 today is MSG09 (login lockout). Recorded as M-03.
