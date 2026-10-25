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

### GET /performance
Status: PLANNED (spec only)
Auth: trader; full dashboard `ADVANCED_PERFORMANCE` (PRO+)
Purpose: Performance statistics (UC-25, SCR-23).
Request/Response/Errors: not defined. FREE sees a reduced dashboard with locks (CR-08).
Source: none. Spec: TD 8, SRS 3.6.3, UC-25, BR-42, BR-62.

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
Status: BUILT 2026-10-25 on `feature/T-080-news-api` (`cdfefd7`, local, stacked on T-079; not merged)
Auth: trader (401 without a session, 403 for ADMIN); every plan sees the same items (D-117, no `NEWS_AI_INSIGHT` gate)
Purpose: News feed, newest first (UC-34, SCR-28; also the news blocks of SCR-08/10/11 with `coin`).
Request (all optional): `coin` symbol, any case (`btc`); `sentiment` `BULLISH|NEUTRAL|BEARISH`, any case; `range` `24h|7d|30d`, any case, **7d by default**; `page` from 1; `pageSize` 1–100, 20 by default.
Response 200 `PageResponse`: `{ items, page, pageSize, total }`; each item
`{ articleId, title, originalTitle, source, originalUrl, publishedAt, summary, aiSummarized, sentiment, coins: [{ symbol, primary }] }`.
- `title`: Vietnamese headline once summarized (D-118), else the collected one; `originalTitle` always the outlet's.
- `summary`: the AI summary (Vietnamese, ≤ 60 words) when `aiSummarized`, else the feed excerpt; may be `null`.
- `sentiment`: absent until the article is summarized (show no chip). `coins`: primary first.
- An unknown `coin` answers an empty page, not an error. Open `originalUrl` in a new tab (SRS 3.8.1).
Errors: 400 with `errors.sentiment`, `errors.range`, `errors.page` or `errors.pageSize` = `MSG15`.
Source: `news/controller/NewsController`. Spec: TD 8, SRS 3.8.1, UC-34, D-117, D-118.

### GET /news/sentiment-summary
Status: BUILT 2026-10-25 (`cdfefd7`, as above)
Auth: trader, every plan (D-117)
Purpose: the 24h summary bar of SCR-28.
Response 200: `{ since, bullish, neutral, bearish }` — articles published since `since` (now − 24 h) per sentiment; articles not summarized yet are not counted.
Source: `news/controller/NewsController`. Spec: TD 8, SRS 3.8.1.

### POST /admin/news-sources/{id}/crawl — crawl now (T-080b, D-119)
Status: BUILT 2026-10-25 on `feature/T-080b-news-admin` (`43ff01a`, local, stacked on T-080; not merged)
Auth: admin. Body: none. Works on a source that is switched off too.
**Confirm first (SCR-41):** before calling, show a dialog built from the source row (`GET /admin/news-sources` or `/{id}`): `crawlIntervalMinutes`, `lastCrawledAt`, `nextCrawlAt`, `active`. Suggested text (vi): *"Nguồn **{sourceName}** được hệ thống tự động crawl **mỗi {crawlIntervalMinutes} phút**. Lần gần nhất: **{lastCrawledAt}** ({n} phút trước). Lần kế tiếp: **{nextCrawlAt}**. Bạn vẫn muốn crawl ngay?"* `[Huỷ]` `[Crawl ngay]`. When `active` is false: *"Nguồn đang tắt, hệ thống không tự crawl."* in place of the next time; when never crawled: *"Chưa crawl lần nào."*
Response 200: the crawl log entry `{ crawlLogId, startedAt, finishedAt, status, articlesFound, articlesInserted, errorMessage }`; then refresh the row (its next crawl is now + interval).
Errors: 404 MSG41; **429 `NEWS_SOURCE_CRAWLED_RECENTLY` MSG50**, `messageArgs[0]` = seconds to wait (crawled less than a minute ago).

### GET /admin/news-articles (T-080b, D-119)
Status: BUILT 2026-10-25 (`43ff01a`, as above). Auth: admin.
Request: `status` `PENDING|FAILED|SUMMARIZED|HIDDEN` (any case), `sourceId`, `page`, `pageSize` (CR-04). Newest first, hidden ones included.
Response 200 `PageResponse` of `{ articleId, sourceId, source, title, aiTitle, originalUrl, excerpt, aiSummary, sentiment, publishedAt, collectedAt, status, summaryAttempts, summaryError, summaryAttemptedAt, hiddenAt }`.
- `FAILED`: no summary after 3 attempts; the job no longer takes it — offer *Tóm tắt lại*. `PENDING` may already carry a `summaryError` from an earlier attempt.
Errors: 400 `errors.status` / `errors.page` / `errors.pageSize` = MSG15.

### POST /admin/news-articles/{id}/hide · /restore (T-080b)
Auth: admin. Response 200: the article (`status` HIDDEN, or its status again). Idempotent; audited on a change (`NEWS_ARTICLE_HIDDEN` / `NEWS_ARTICLE_RESTORED`). A hidden article leaves `GET /news` and `/news/sentiment-summary`. Errors: 404 MSG41.

### POST /admin/news-articles/{id}/summarize (T-080b)
Auth: admin. Waits for the model (show a spinner; up to about 2 minutes). Replaces any summary. Response 200: the article — `SUMMARIZED`, or the refusal in `summaryError` (an article that had a summary keeps the old one). Errors: 404 MSG41; **503 `NEWS_SUMMARY_UNAVAILABLE` MSG31** (AI Service not configured, down or rate limited).

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
| `/admin/pairs` | UC-45 (MSG40) | T-085 |
| `/admin/leverage-brackets` | UC-46 | T-085 |
| `/admin/packages` | UC-47 | T-066+ |
| `/admin/orders` | UC-48 | T-066+ |
| `/admin/news-sources` | UC-49 | T-077 — **built 2026-10-25** on `feature/T-077-news-source-model` (local, not merged): `GET`, `POST` (201; feed read first, 400 `NEWS_FEED_UNREADABLE` with `errors.feedUrl` MSG15, 409 `NEWS_SOURCE_ALREADY_REGISTERED`), `GET/PUT/DELETE /{id}` (DELETE 204, 409 `NEWS_SOURCE_IN_USE`), `GET /{id}/crawl-logs?page=&pageSize=` (PageResponse, latest first). Interval < 15 → `errors.crawlIntervalMinutes` MSG15 (BR-49). Response: `sourceId, sourceName, feedUrl, sourceType, crawlIntervalMinutes, active, categoryFilter, bodySelector, excludedSelectors, userAgent, lastCrawledAt, lastCrawl{startedAt,status,articlesFound,articlesInserted}, nextCrawlAt, createdAt, updatedAt`; `status` ∈ SUCCESS, PARTIAL, FAILED |
| `/admin/ai-configurations` | UC-50 | T-071/T-073 |
| `/admin/settings` | UC-51 | T-082 |
| `/admin/audit-log` | UC-52 | T-081 writer done; read API not built |
| `/admin/announcements` | UC-44 | T-084 |

Status: PLANNED (spec only) for all 13. Source: none. Spec: TD 8, SRS 3.11.
