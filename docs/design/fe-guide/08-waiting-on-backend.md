# Requests from the web to the backend

What the web client (and later the mobile app) needs the backend to **fix, push or build**. Section 1
lists defects found while testing the web against the running backend, each with its cause, the
proposed fix and the test that proves it; the other sections list the hard dependencies that keep a web
task from moving. Choices the web can make on its own side are not asked here.

| | |
|---|---|
| Backend read | `develop` @ `612b201` (PR #65, 2026-10-23; migrations V30, V31), re-read 2026-10-24; first read `796f408` (PR #64) with migrations up to V29; `feature/TP-A-plan-validity` @ `112aa24` (rebased on `612b201`, force-pushed, not merged) |
| Web client | `cryptopilot-frontend` `develop` @ `fd7a485` (community, notifications and moderation on HTTP) and the local branch `feature/T-087-announcements` @ `8cb12bc` (UC-44) |
| How it was found | Browser run against the backend (Edge, 1440 and 390 px): 13 web workflows of T-065, T-059 and T-087, STOMP frames captured, backend log read |
| Date | 2026-10-23; re-checked 2026-10-24 |
| Owner of this file | FE; a row leaves when its fix or API is on `develop` (name the merge commit in `CHANGELOG.md`) |

Question ids (Q-xx), decisions (D-xx) and task ids come from `CURRENT_STATE.md` sections 4, 6 and 8,
which stay the source of truth for their status. Per-endpoint status stays in `06-task-map.md` and the
module files.

## Summary

| # | Request | Kind | Backend owner | Priority | Blocks on the web |
|---|---|---|---|---|---|
| 1 | Q-75: let a signed-in session subscribe to `/user/queue/notifications` | Defect | BE2 (notification) | **High**, one line and a test | Live bell (T-059); the web polls every 60 s meanwhile |
| 2 | Q-76: opening a moderation case must not fail when two openings meet | Defect | BE2 (community) | Medium | Nothing today (the web sends one opening); two Admins see a false MSG43 |
| 3b | Q-81: let an Admin sign a media upload for an announcement | Defect | BE2 (community) | Medium | Images and video in announcements (T-087); the web form omits media meanwhile |
| 3c | Q-83: cache the Futures last price from the 1m klines (`MarketStreamSupervisor` returns before the cache) | Defect | BE1 (market) | **High**, one branch and a test | Every Futures MARKET plan, Futures invalidation price and Futures STOP activation (T-040) answers 503 MSG43 |
| 4 | Push `feat/t-085-pair-admin`, `feat/t-082-system-settings`, `feat/t-083-user-management`, `feat/t-086-reports` and open their PRs | Release | BE2 | **High** | Admin screens SCR-33…44 (T-087); Futures plans (T-040), since `leverage_bracket` is empty |
| 5 | Merge PR #66 of `feature/TP-A-plan-validity` (Q-74 and Q-77 answered; one approval, 2026-10-24) | Release | BE1 | Medium | GY-03 scope of T-040 / T-041 (invalidation price, INVALIDATED; STOP stays hidden until TP-B) |
| 6 | Missing data in existing endpoints: FEQ-02, M-09, Q-21, Q-31, FEQ-04 | Gap | see section 3 | Low…medium | see section 3 |
| 7 | APIs not built yet | Tasks | see section 4 | Planned | see section 4 |

## 1. Defects (found 2026-10-23 on `develop` `796f408`)

Re-checked 2026-10-24 on `develop` `612b201` (PR #65): Q-75 and Q-76 are unchanged
(`WebSocketConfig.java:74`, `ModerationServiceImpl.open`). Q-70 landed (section 5).

### 1.1 Q-75 — the notification push is refused, and the refusal closes the account's connection

**Symptom.** After sign-in the web opens the account's STOMP connection with the access token and
subscribes to the notification queue. The backend accepts the connection, then refuses the
subscription with an ERROR frame and closes the connection. Frames captured in the browser:

```
>> CONNECT    Authorization:Bearer eyJ…
<< CONNECTED  user-name:01a166fc-e807-…           (the session is signed in)
>> SUBSCRIBE  id:sub-0  destination:/user/queue/notifications
<< ERROR      message:not a public market topic: /user/queue/notifications
   (the connection closes; the client reconnects with back-off and is refused again)
```

**Cause.** The writer and the subscription guard disagree:

- `notification/service/impl/NotificationWriter.java:35` and `:85` send each new notification with
  `convertAndSendToUser(recipientId, "/queue/notifications", body)`, which the client receives on
  `/user/queue/notifications` (E-1, TD 9).
- `common/config/WebSocketConfig.java:74` admits only the demo trading queues:
  `USER_QUEUES = Pattern.compile("/user/queue/(orders|fills|balances)")`. In `requireAllowed`
  (`:162`–`:180`) any destination outside `USER_QUEUES` is checked against `PUBLIC_TOPICS` and refused
  with `MessageDeliveryException("not a public market topic: …")`.
- No test subscribes to `/user/queue/notifications`, so CI did not see it.

**Impact.** A STOMP ERROR frame ends the whole connection, not one subscription. The web carries every
user queue on one signed-in connection, so subscribing to notifications would also cut the demo
trading pushes (`/user/queue/orders`, `fills`, `balances`, TR-08) and make the client reconnect again
and again. The web therefore does **not** subscribe today: the bell reads `GET /notifications/unread-count`
every 60 s (TD 9 fallback), so a new notification shows up to a minute late.

**Requested fix.**

```java
/** The queues of the signed-in user: demo trading (TR-08) and in-app notifications (E-1). */
static final Pattern USER_QUEUES =
        Pattern.compile("/user/queue/(orders|fills|balances|notifications)");
```

Update the class Javadoc ("What a client may subscribe to") with the new queue.

**Test.** In the `requireAllowed` tests: a signed-in session may subscribe to
`/user/queue/notifications`; an anonymous session is refused with "sign in to subscribe". End to end:
a comment on another member's post reaches the author's subscription.

**Web follow-up.** Pass the signed-in feed to the notification adapter (one line in the service
wiring) and re-run the browser check; T-059 then closes its SCR-15 part.

### 1.2 Q-76 — two openings of the same reported post: the second answers 409

**Symptom.** An Admin opens a reported post on SCR-36 and the dialog shows MSG43 instead of the post.
Backend log:

```
WARN GlobalExceptionHandler: A concurrent change won the optimistic lock …
  update post_report set resolution_action=?, resolved_at=?, resolved_by=?, report_status=?,
  updated_at=?, version=? where report_id=? and version=?
  (expected row count 1 but was 0) for entity PostReport
```

The request answers `409 DATA_CONFLICT` (MSG43).

**Cause.** `GET /admin/reports-queue/{postId}` reads and writes:

- `community/service/impl/ModerationServiceImpl.java:100`–`:104` (`open`) loads the OPEN and
  REVIEWING reports of the post, calls `PostReport.review()` on each (OPEN → REVIEWING,
  `community/entity/PostReport.java:81`) and flushes.
- `PostReport` extends `BaseEntity`, whose `version` column is an optimistic lock.

Two openings at the same moment both read the reports as OPEN at version 0; the first commits
REVIEWING at version 1; the second updates `where version = 0`, finds no row and fails. Only the first
opening of a post can conflict: once its reports are REVIEWING, `review()` changes nothing and nothing
is written.

**When it happens.** Two Admins open a newly reported post together, or a client sends the opening
again after a timeout or an aborted request (an abort in the browser does not stop the server, which
commits the first opening anyway). The web hit the second case in development (a remount aborted and
re-sent the call); it now sends the opening once and never aborts it (web commit `d717474`). Two
Admins can still meet it.

**Requested fix** (one of, in order of preference):

1. Claim the reports with one conditional statement instead of entity dirty checking:
   `UPDATE post_report SET report_status = 'REVIEWING', version = version + 1, updated_at = now()
   WHERE post_id = :postId AND report_status = 'OPEN'`, then read the reports. A concurrent opening
   updates 0 rows and succeeds.
2. Catch `ObjectOptimisticLockingFailureException` in `open` and read once more (the reports are then
   REVIEWING, so the second read writes nothing).
3. Keep the behaviour and document that a 409 here means "opened elsewhere, read again"; the web will
   then retry once instead of showing MSG43.

**Test.** Two concurrent openings of a post with OPEN reports both answer 200 with the same reports,
which end REVIEWING with their version raised once.

### 1.4 Q-81 — an Admin cannot attach media to an announcement

**Symptom.** With an Admin's token, `POST /media/upload-signature` answers `403 ACCESS_DENIED`
(MSG43), so the announcement form cannot upload an image or a video (checked on `develop` `796f408`).

**Cause.** The announcement API accepts media but the signing endpoint is closed to the Admin:

- `community/controller/AnnouncementController.java` takes a `PostRequest` with `media`, and
  `PostWriter.create` checks the files for an official post (video allowed without `VIDEO_POST`,
  because the author is not a Trader).
- `auth/config/SecurityConfig.java` lists `/api/v1/media/**` in `TRADER_AREA`, which only the TRADER
  role may call; `ADMIN_CONSOLE` covers `/api/v1/admin/**` only.

SRS 3.7.2 gives the Admin the same form "with the option Official", media included.

**Requested fix** (one of):

1. Allow ADMIN on `POST /media/upload-signature` (list it with the paths both roles may call, as
   `SHARED_PASSWORD_CHANGE` is, or add `/api/v1/admin/media/upload-signature`), with the files in the
   Admin's own folder as for a Trader.
2. Or state in the SRS and the API that announcements carry no media.

**Test.** An Admin signs a form, uploads, and publishes an announcement that names the file; a Trader
still cannot use an Admin endpoint.

**Web follow-up.** Show the media block of the form in the Official mode (one condition) and check the
upload against the backend.

### 1.5 Q-83 — the Futures last price is never cached (checked 2026-10-25 on `develop` `dccfc6c`)

**Symptom.** With live streams, `POST /plans/calculate` of a Futures MARKET plan answers
`503 MARKET_PRICE_UNAVAILABLE` (MSG43) while Futures LIMIT plans calculate; the Redis hash
`px:FUTURES:BTCUSDT` holds `mark`, `index`, `funding`, `nextFundingTime` and `updatedAt`, but no `last`.

**Cause.** `market/job/MarketStreamSupervisor.java`, `onMessage`: a `KlineMessage` of interval
`ONE_MINUTE` goes to `toMinuteListeners` and the method returns, before `updates.onUpdate(market,
message)`. `PriceCacheServiceImpl.record` writes the Futures last price only from those 1m klines
(TP-0), so it is never written. `PriceCacheServiceTest` calls `record` directly, so CI passes.

**Requested fix.** Hand the 1m klines to `updates.onUpdate` as well after the minute listeners (or record
them in the price cache before returning), and test it through the supervisor: a futures 1m kline makes
`latestLast` FOUND.

**Web follow-up.** None: SCR-17 already shows "price unavailable" with Try again on the 503, and the
expected fill appears once the backend answers it.

## 2. Branches to push

| Branch (owner) | Status in `CURRENT_STATE.md` section 6 | Why the web needs it now |
|---|---|---|
| `feat/t-085-pair-admin` → `feat/t-082-system-settings` → `feat/t-083-user-management` → `feat/t-086-reports` (BE2), stacked, local | T-085, T-082, T-083, T-086 **DONE** 2026-10-21, not pushed | The web cannot read their contracts, so SCR-33…44 of T-087 cannot start. T-085 also fills `leverage_bracket`: the table is empty on `develop` (0 rows in a database migrated to V29), so every Futures plan calculation answers 400 `errors.leverage` (M-12) and the Futures plan form of T-040 waits |
| `feature/TP-A-plan-validity` (BE1), pushed, PR #66 open with one approval | TP-A DONE (Q-74 and Q-77 answered) | T-040 and T-041 gained GY-03 scope (D-111, D-112): STOP entry, invalidation price, INVALIDATED status. The web builds it against the merged contract and keeps STOP hidden until TP-B |

## 3. Missing data in existing endpoints

| Id | What the web needs | Checked on `796f408` | Web work blocked |
|---|---|---|---|
| FEQ-02 | The caller's plan: tier, limits (`ACTIVE_PLAN_MAX`, `WATCHLIST_MAX` …), end date and usage, e.g. in `GET /me/profile` or `GET /billing/subscription` | Still missing: `billing` has no controller, the profile has no plan fields | Lock icons before a request (CR-08) on SCR-10/11/14; Subscription tab of SCR-07; "x of y" limits on SCR-08 |
| M-09 | Futures last price and 24h statistics (last, change, high, low, quote volume) | Still missing: `FuturesStatsResponse` carries mark, index, funding, open interest, long/short ratio | Futures tab of SCR-09 and the SCR-11 header as SRS 3.3.1 describes them (mark price shown meanwhile) |
| Q-82 | The maximum leverage of a Futures pair (`maxLeverage` in `GET /market/pairs`) and a Trader read of its brackets | Missing on `dccfc6c`: only `GET /admin/pairs/{id}/brackets` (ADMIN) | SCR-17 shows no maximum or leverage slider; a refusal says "above the maximum for this position size, or no brackets" |
| Q-21 | Analysis push on each closed candle | RESOLVED (D-126), branch `feat/t-029-analysis-push` | Subscribe to the analysis topic; re-read `GET /analysis` for the score when a message arrives |
| Q-31 | Marker of alerts paused by a plan change | OPEN; PROPOSED 2026-10-22 `paused_reason` | BR-64 mark on SCR-13 |
| FEQ-04 | Indicator series | OPEN (not re-checked) | The web computes the series for drawing (ADR-017) |

## 4. APIs not built yet (hard dependencies)

| Backend task (owner) · status | API the web needs | Web work blocked |
|---|---|---|
| T-046 (BE2) · TODO | `POST /plans/{id}/close-position`, position status and P/L on plan rows (M-10), `/user/queue/positions` (M-06) | Close position dialog (T-047, SCR-19); live position on plan detail (T-041); open positions on SCR-08 |
| T-048…T-051 (BE2) · TODO | `/journal/**`, `GET /performance` | Journal, entry detail, manual trade, performance (T-052, SCR-20…23); performance block of SCR-08 (T-112) |
| T-066…T-070 (BE1) · TODO | `/billing/**` | Packages, checkout, payment result, payment history (T-071, SCR-30…32) |
| T-072 (DO), T-073…T-075 (BE1) · TODO | `/ai/**`, `/user/queue/ai` | AI assistant (T-076, SCR-29) |
| T-077…T-079 (BE2) · TODO | `GET /news`, `GET /news/sentiment-summary` | News feed (T-080, SCR-28); news block of SCR-08 (T-112) |
| TR-14…TR-17 · TODO, owner TBD | Leverage and margin mode, Futures orders, positions, close, add or remove margin | Demo Futures trading (TR-F4) and the Futures part of TR-F5 |
| TR-25, TR-28 · TODO, owner TBD | Modify a LIMIT order, the calculator, PnL analysis by period | TR-F5 drag to modify, calculator, daily PnL chart |
| TR-35 · TODO, owner TBD | Running candle for every timeframe, 16 timeframes of history | TR-F2 16 timeframes |
| T-058 (DO) · TODO | FCM sending | Push notifications and deep links on mobile (T-092) |

## 5. Done since the previous version (2026-10-13)

| Row | Landed |
|---|---|
| FEQ-01 pair id in `GET /market/pairs` | fix `5ef54e1`, on `develop` |
| Demo trading module (TR-02…TR-13) | on `develop` (web re-check on `4f9003a`, 2026-10-20); web flag removed (`e9d9223`) |
| Notification read API (list, unread count, mark read, mark all) | PR #64, `796f408` (push: Q-75) |
| Community, moderation and announcement API (T-060…T-064, T-084, CF-01…CF-04) | PR #63 and PR #64, `796f408` |
| Q-70 idempotency key for order lists: `listClientOrderId` (the exchange's name, not `clientListOrderId` as asked); the same key answers 200 with the group already placed, a new one 201 | PR #65, `612b201`; the web sends it (TR-F3, branch `feature/TR-F3-spot-filters`) |

## 6. Keeping this file current

When a fix or an API reaches `develop`: move its row to section 5 with the merge commit, add a line to
`CHANGELOG.md`, update `06-task-map.md` and the FE task row in `CURRENT_STATE.md`, and change the
"Backend read" line.
