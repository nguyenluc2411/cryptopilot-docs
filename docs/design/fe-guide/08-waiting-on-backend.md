# FE work waiting on the backend

What the web client (and later the mobile app) cannot build or release until the backend builds an
API or the team answers a question. It is the request list from FE to BE: each row names what is
missing, who owns it, and what FE does meanwhile.

| | |
|---|---|
| Backend read | `develop` @ `233fcc8` (PR #53, 2026-10-08); demo trading branch `feat/tr-02-paper-trading-schema` @ `f4e66b2` (not merged); open PRs #49, #51, #54 change no API |
| Web client | `cryptopilot-frontend` `develop` @ `0564ceb` (2026-10-13) |
| Date | 2026-10-13 |
| Owner of this file | FE; updated when a row is unblocked or a new wait appears |

Task ids, owners and statuses come from `CURRENT_STATE.md` section 6; questions from section 8 and
`07-open-questions.md`. The per-endpoint status stays in `06-task-map.md` and the module files.

## 1. What unblocks the most (in order)

| # | Ask to BE / team lead | Unblocks on the web | Size on the BE side |
|---|---|---|---|
| 1 | **FEQ-01 — give the client a pair's id.** Add `pairId` to each row of `GET /market/pairs` (or accept `symbol` where a `pairId` is required), and the pair symbol in plan rows (M-10) | Create plan (T-040), Add to watchlist (T-059), pair name and chart in the plan list and detail (T-041), demo orders on any pair and the pair filter of the demo Orders page (TR-F3) | One field in `PairResponse` (and one in `TradingPlanSummaryResponse`); a team lead decision first |
| 2 | **Merge the demo trading module** (`feat/tr-02-paper-trading-schema`: TR-03…TR-07, D-86) into `develop` | Release of the demo trading screens TR-F1…TR-F3 and the Spot part of TR-F5. The web code is already on `develop`, hidden behind `VITE_ENABLE_PAPER_TRADING`, and tested end to end against `f4e66b2` | Review and merge; tell FE if the contract changes, FE re-checks before the flag is turned on |
| 3 | **T-046** manual close, plan expiry and `/user/queue/positions` (BE2) | Close position dialog and position status (T-047, SCR-19), live position block in plan detail (T-041), open position details on the dashboard (T-111) | Planned |
| 4 | **T-056** outbox processor and notification dispatch (DO), with the `/notifications/**` API | Notification center (SCR-15, T-059), alert trigger history (T-059), recent notifications on the dashboard (T-111) | Planned |
| 5 | **TR-08** user queue STOMP for orders, fills and balances (owner TBD) | Live demo orders, fills and wallets; the web reads them every 3 s meanwhile | Planned |

## 2. FE tasks and what each waits for

| FE task | Screens | Waits for (BE task, owner) | What FE needs exactly | FE meanwhile |
|---|---|---|---|---|
| T-031 Public home and market list | SCR-01, SCR-09 | M-09 (no task yet) | Futures last price and 24h change, high, low, quote volume in `futures/{symbol}/stats` and the Futures ticker topic | Futures tab shows mark price and funding only |
| T-033 / T-034 Analysis | SCR-10, SCR-11 | T-107 plan gates (BE1, READY); FEQ-02 | The server refusing what a FREE plan may not see (MSG29), and a way to read the caller's tier and limits before a request | Locks shown from the session's entitlements (display only, D-58) |
| T-040 Create / edit plan | SCR-17 | FEQ-01; T-085 leverage brackets (BE2) | `pairId` from the market list; Futures brackets (every Futures call answers 400 `errors.leverage` today, D-70) | Edit of a DRAFT only, Spot only |
| T-041 Plan list and detail | SCR-16, SCR-18 | FEQ-01 / M-10; T-046 (BE2) | Symbol in plan rows; position status, P/L and close for EXECUTED plans | Pair taken from the watchlist when known; position block says it waits |
| T-047 Close position dialog | SCR-19 | T-046 (BE2) | `POST /plans/{id}/close-position`, `/user/queue/positions`, MSG21 | Not started |
| T-052 Journal and performance | SCR-20…23 | T-048, T-049, T-050, T-051 (BE2) | `/journal/**`, `GET /performance` | Not started; routes show a placeholder |
| T-059 Watchlist, alerts, notifications | SCR-12…15 | FEQ-01; T-110 (BE2); T-056 (DO); Q-30; Q-31 | Add pair; INDICATOR, OPEN_INTEREST_CHANGE and FUNDING_RATE alerts evaluated; `/notifications/**`; FUNDING_RATE threshold unit; "paused by a plan change" mark | Watchlist and PRICE alerts work; Add pair, notification center and the two marks wait |
| T-111 Trader dashboard | SCR-08 | T-056 (DO), T-051 (BE2), T-079 (BE2), T-046 (BE2) | Notifications, performance summary, latest news, open position details | Those blocks say they are not connected |
| T-065 Community | SCR-24…27 | T-060, T-062, T-063, T-064 (BE2), T-061 (DO) | `/posts/**`, `/comments/**`, `/media/upload-signature`, reports | Not started |
| T-071 Packages and payment | SCR-30…32 | T-066…T-070 (BE1); FEQ-05 | `/billing/**`; which URL the browser returns to after payment | Not started |
| T-076 AI assistant | SCR-29 | T-072 (DO), T-073…T-075 (BE1) | `/ai/**`, `/user/queue/ai` | Not started |
| T-080 News feed | SCR-28 | T-077…T-079 (BE2) | `GET /news`, `GET /news/sentiment-summary` | Not started |
| T-087 Admin console | SCR-33…44 | T-082…T-086 (BE2) and the rest of `/admin/**` | Admin endpoints (only `PUT /me/password` exists for admins) | Only the admin account page is built |
| TR-F3 Demo Spot orders, wallet, transfer | — (D-86) | Merge of the paper module; Q-46; TR-08 | Fee rates readable by the client (Q-46); pushed orders, fills and balances (TR-08) | Built behind the flag; no fee estimate; polling every 3 s |
| TR-F2 Order book | — (D-86) | Q-45 | A book deeper than 20 levels for price grouping (10×, 100×, 1000× tick) | Four groups offered on 20 levels |
| TR-F4 Demo Futures | — (D-86) | TR-14, TR-15, TR-16, TR-17 (owner TBD) | Leverage and margin mode, Futures orders, positions, close and margin APIs | Not started |
| TR-F5 Rest of chart tools | — (D-86) | TR-25, TR-28 (owner TBD); TR-35 | Modify a LIMIT order (drag on the chart), calculator, PnL analysis API; more timeframes | Spot order lines and fill markers done |
| Mobile T-089…T-092 | SCR-08…21 | As their web tasks; T-058 (DO) for push | Same as the rows above; FCM sending for T-092 | T-088 is not blocked; mobile is postponed by the FE owner |

## 3. Questions that need an answer (no code missing, a decision is)

| Id | Question, in short | Asked of | FE meanwhile |
|---|---|---|---|
| FEQ-01 | How does the client get a pair's `id`? (section 1, row 1) | Team lead + BE | Watchlist rows are the only source of pair ids |
| FEQ-02 | How does the client learn the caller's plan tier and limits before a request? | Team lead + BE1 | Session entitlements; the backend still decides every request |
| FEQ-03 | Which web route and query parameter do the verification and reset emails link to? | DO (T-057) | `/verify-email?token=`, `/reset-password?token=` assumed |
| FEQ-05 | Where does the browser land after a payment: the web route or `GET /billing/return/{gateway}`? | BE1 (T-067…T-069) | Not started |
| Q-21 | How is the analysis pushed (destination and payload)? | Team lead | The web reads the analysis again on each closed candle |
| Q-30 | Unit of a FUNDING_RATE alert threshold (fraction or percent) | Team lead | The FUNDING_RATE input is not offered |
| Q-31 | Marker for alerts paused by a plan change (BR-64) | Team lead | No mark on SCR-13 |
| Q-43 | MSG50: "already reported" or rate limit? | Team lead | The web branches on the error `code` for 429 |
| Q-44 | Where does the browser keep the refresh token? FE proposes an `HttpOnly` cookie set by `/auth/login` and `/auth/refresh` | Team lead + BE | Access token in memory only, so a page reload signs the user out |
| Q-45 | Deeper order book for price groups: stream `@depth` with a snapshot of up to 1,000 levels, or keep 20 levels and offer the tick and 10× only? | BE (TR-03 owner) | Four groups on 20 levels |
| Q-46 | Expose the paper fee rates (`cryptopilot.paper.spot-maker-fee-rate` / `spot-taker-fee-rate`), e.g. in `GET /paper/account` | BE (TR-06 owner) | No fee estimate in the order form |

## 4. Already usable, not blocked

- The demo trading branch accepts post-only LIMIT orders (`timeInForce: GTX`; one that would take
  liquidity expires with `statusReason: POST_ONLY_WOULD_TAKE`, checked against `f4e66b2`). The web form
  offers GTC, IOC and FOK only; FE can add it. The javadoc of `PlaceOrderRequest` still says "GTC, IOC
  or FOK".
- `GET /paper/orders/{orderId}` (one order) exists on the branch; the web has no order detail view yet.
- T-088 Flutter skeleton: its auth API is on `develop`.

## 5. Keeping this file current

When a backend PR merges or a question is answered: move the row out (or mark it done with the merge
commit), update `06-task-map.md` and the FE task row in `CURRENT_STATE.md`, and change the "Backend
read" line above.
