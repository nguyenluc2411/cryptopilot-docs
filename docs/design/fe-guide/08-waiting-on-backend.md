# FE work waiting on the backend

What the web client (and later the mobile app) **cannot build** because the backend has no API or no
data for it yet. Only hard dependencies are listed: improvements FE can live without (pushed updates,
more timeframes, server-side enforcement of rules FE already shows) and choices FE can make on its own
side are handled by FE and are not asked here.

| | |
|---|---|
| Backend read | `develop` @ `233fcc8` (PR #53, 2026-10-08); demo trading branch `feat/tr-02-paper-trading-schema` @ `f4e66b2` (not merged); open PRs #49, #51, #54 change no API |
| Web client | `cryptopilot-frontend` `develop` @ `0564ceb` (2026-10-13) |
| Date | 2026-10-13 |
| Owner of this file | FE; a row leaves when its API is on `develop` |

Task ids and owners come from `CURRENT_STATE.md` section 6; the per-endpoint status stays in
`06-task-map.md` and the module files.

## 1. Missing data in existing endpoints (small, unblocks the most)

| # | What FE needs | Why FE cannot do without it | FE work blocked |
|---|---|---|---|
| 1 | **A pair's id (FEQ-01).** `pairId` in each row of `GET /market/pairs`, or `symbol` accepted wherever a `pairId` is required; and the pair `symbol` in plan rows (`TradingPlanSummaryResponse`, M-10) | `POST /watchlist`, `POST /plans`, `POST /alerts`, `POST /paper/orders` take a `pairId`, and no read returns it for a symbol. The only source is a watchlist row, and adding a row needs the id itself | Create plan (T-040, SCR-17); Add to watchlist (T-059, SCR-12); pair name and chart in the plan list and detail (T-041, SCR-16/18); demo orders on a pair outside the watchlist and the pair filter of the demo Orders page (TR-F3). **2026-10-14:** backend `fix/feq-01-pair-id` (`5ef54e1`) adds `pairId` to `GET /market/pairs`; FE `fix/FEQ-01-pair-id` (`799753d`) uses it for demo trading. Row stays until the backend PR is on `develop` (and merged into the demo trading branch) |
| 2 | **The caller's plan (FEQ-02).** Tier, limits (`ACTIVE_PLAN_MAX`, `WATCHLIST_MAX`, …), end date and usage, e.g. in `GET /me/profile` or `GET /billing/subscription` | No endpoint reports the plan; the web session holds `entitlements: unknown` against the real backend, so nothing can be shown or locked up front | Lock icons on features the plan lacks (CR-08) on SCR-10/11/14; Subscription tab of SCR-07; "x of y" plan limits on the dashboard (T-111) |
| 3 | **Futures last price and 24h statistics (M-09).** Last price, 24h change, high, low, quote volume in `GET /market/futures/{symbol}/stats` and the Futures ticker topic | They carry mark, index and funding only | Futures tab of the market list (T-031, SCR-09) and the Futures analysis header (T-034, SCR-11) as SRS 3.3.1 describes them |

## 2. APIs that do not exist yet

| # | Backend task (owner) | API FE needs | FE work blocked |
|---|---|---|---|
| 4 | T-046 (BE2) | `POST /plans/{id}/close-position`, `/user/queue/positions`, position status and P/L of an EXECUTED plan | Close position dialog (T-047, SCR-19); live position block of plan detail (T-041); open position details on the dashboard (T-111) |
| 5 | T-085 (BE2) | Leverage brackets, so Futures plans calculate (every Futures call answers 400 `errors.leverage` today, D-70) | Futures plans (T-040) |
| 6 | T-056 (DO) | `/notifications/**` (list, unread count, mark read) and the alert trigger history | Notification center (T-059, SCR-15); recent notifications on the dashboard (T-111) |
| 7 | T-048…T-051 (BE2) | `/journal/**`, `GET /performance` | Journal, entry detail, manual trade, performance (T-052, SCR-20…23); performance block of the dashboard (T-111) |
| 8 | T-060…T-064 (BE2), T-061 (DO) | `/posts/**`, `/comments/**`, `/media/upload-signature`, reports | Community (T-065, SCR-24…27) |
| 9 | T-066…T-070 (BE1) | `/billing/**` | Packages, checkout, payment result, payment history (T-071, SCR-30…32) |
| 10 | T-072 (DO), T-073…T-075 (BE1) | `/ai/**`, `/user/queue/ai` | AI assistant (T-076, SCR-29) |
| 11 | T-077…T-079 (BE2) | `GET /news`, `GET /news/sentiment-summary` | News feed (T-080, SCR-28); news block of the dashboard (T-111) |
| 12 | T-082…T-086 (BE2) and the rest of `/admin/**` | Admin endpoints (only `PUT /me/password` exists for admins) | Admin console (T-087, SCR-33…44) |
| 13 | TR-14…TR-17 (owner TBD) | Leverage and margin mode, Futures orders, positions, close, add or remove margin | Demo Futures trading (TR-F4) |
| 14 | TR-25, TR-28 (owner TBD) | Modify a LIMIT order, the calculator endpoints, PnL analysis | Rest of TR-F5 (drag an order on the chart, calculator, PnL analysis) |
| 15 | T-058 (DO) | FCM sending | Push notifications and deep links on mobile (T-092) |

## 3. Release

| # | What | Why |
|---|---|---|
| 16 | Merge the demo trading module (`feat/tr-02-paper-trading-schema`) into `develop` | The demo trading screens (TR-F1…TR-F3, Spot part of TR-F5) are built and tested against `f4e66b2`, but stay hidden behind `VITE_ENABLE_PAPER_TRADING` until the module is merged. Tell FE if its contract changes before the merge |

## 4. Keeping this file current

When one of these APIs reaches `develop`: remove its row (name the merge commit in `CHANGELOG.md`),
update `06-task-map.md` and the FE task row in `CURRENT_STATE.md`, and change the "Backend read" line.
