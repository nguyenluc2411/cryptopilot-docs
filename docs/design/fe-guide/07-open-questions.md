# 07 · Open questions and spec-vs-code mismatches

This file records; it does not decide. Each item cites both sources. Answers belong to the team lead
and go to `CURRENT_STATE.md` (Q-xx, D-xx, A-xx); then this file is updated.

Code paths are relative to the `cryptopilot_project` root at `0d92def` unless a branch is named.

## A. Existing open questions that affect FE (`CURRENT_STATE.md` section 8)

| Id | Question (short) | Affects | Status |
|---|---|---|---|
| Q-21 | Analysis push: destination, payload, CONNECT authentication | T-032…T-034 live analysis | OPEN — until answered, re-read `GET /analysis` on each closed kline |
| Q-30 | Unit of a FUNDING_RATE alert threshold (fraction vs percent) | T-059 alert dialog (SCR-14) | OPEN — do not ship the FUNDING_RATE input yet |
| Q-31 | Marker for alerts paused by a plan change (BR-64), and whether resume clears it | T-059 alert list (SCR-13) | OPEN |
| Q-06 | Flutter chart library (ADR-012) | T-090 | OPEN |
| Q-07 | Staging host and domain; single backend instance | Base URLs, CORS origins, WS origins (01-setup) | OPEN |
| Q-02 | Quantitative targets of SRS 4.2 (response times) | Loading states, timeouts | OPEN |

SRS alignment items whose interim answer the client sees (`CURRENT_STATE.md` section 5):

| Id | What FE sees today |
|---|---|
| A-17 | `DATA_CONFLICT` borrows MSG43 (no "duplicate" message) |
| A-20 | Password confirmation mismatch shows MSG03 under `confirmPasswordMatching` |
| A-24 | 403 `ACCESS_DENIED` borrows MSG43 |
| A-28 | `forgot-password` has no server throttle |
| A-36 | Resend limit answer (429, MSG46) undecided in detail; not built (T-105) |
| A-38 | Plan status conflicts borrow MSG43 |
| A-39 | `MARKET_PRICE_UNAVAILABLE` borrows MSG43 |

## B. New questions raised by this guide (FEQ-xx)

Not yet in `CURRENT_STATE.md` section 8; the team lead may promote them to Q-xx.

| Id | Question | Why it blocks FE | Sources |
|---|---|---|---|
| FEQ-01 | How does the client obtain a pair's `id`? `POST /watchlist`, `POST /plans`, `POST /alerts` and `GET /plans?pairId=` take a `pairId` (UUID), but `GET /market/pairs` returns no id, and plan rows return `pairId` without a symbol. Options seen in code: add `pairId` to `PairResponse`, or accept `symbol` in the requests | "Add to Watchlist", "Create Trading Plan", "Create Alert" cannot be built from market screens; the plan list cannot show the pair | `backend/src/main/java/com/cryptopilot/market/dto/response/PairResponse.java#L21`; `backend/src/main/java/com/cryptopilot/watchlist/dto/request/AddWatchlistItemRequest.java#L16`; `backend/src/main/java/com/cryptopilot/trading/dto/request/CreateTradingPlanRequest.java#L36`; `backend/src/main/java/com/cryptopilot/trading/dto/response/TradingPlanSummaryResponse.java#L32`. Spec: TD 8 (watchlist row "the pair is named by `pairId` as in `POST /plans`"), D-75, SRS 3.5.2 (column "pair") **Answered 2026-10-14 by the backend (`fix/feq-01-pair-id`, in `develop`):** every row of `GET /market/pairs` carries `pairId` (`PairResponse.java#L25` at `4f9003a`), one id per symbol on both markets (checked 2026-10-20). Web side done 2026-10-20 (`a84ef89`): the id is required; watchlist, alerts, plans (names, pair filter, SCR-18 chart) and demo orders use it |
| FEQ-02 | How does the client learn the caller's plan tier and limits before a request? | CR-08 asks for lock icons on features the plan lacks; SCR-07 Subscription tab shows plan, end date and usage. Only `GET /watchlist` → `limit` exists. `GET /billing/subscription` is planned (T-066+) but P10 is Sprint 8 | `backend/src/main/java/com/cryptopilot/billing/model/enums/Feature.java#L13` (no controller in `billing`). Spec: CR-08, SRS 3.1.3, 3.2.5, TD 8 |
| FEQ-03 | What URL does the verification / reset email link to (web route and query parameter name)? | SCR-03 and SCR-06 must parse it; mobile deep links (T-092) too | No mail template in code (T-057). Spec: SRS 3.2.2, 3.2.4 **Answered 2026-10-13 by D-108:** `/verify-email?token=`, `/reset-password?token=` |
| FEQ-04 | Where do indicator **series** for chart overlays come from? `GET /analysis` returns the latest values only | SRS 3.3.2 draws SMA20, EMA20/50/200, Bollinger as overlays and RSI/MACD/Volume SMA as panels over 500 candles. Without a series the client must compute them itself (BR-12, D-52/D-55 variants) and could disagree with the server's score inputs | `backend/src/main/java/com/cryptopilot/market/dto/response/IndicatorsResponse.java#L24`. Spec: SRS 3.3.2, BR-12, TD 8 (analysis row) |
| FEQ-05 | Which component receives the browser after payment: the web route in `deploy/.env.example` (`VNPAY_RETURN_URL`, `MOMO_REDIRECT_URL` → `http://localhost:5173/payment/result`) or `GET /billing/return/{gateway}` (TD 8)? | T-071 routing | `deploy/.env.example`. Spec: TD 5.3, TD 8 |

## C. Spec-vs-code mismatches

| Id | Topic | Spec says | Code does | FE workaround |
|---|---|---|---|---|
| M-01 | Pair id | TD 8 / D-75: requests name the pair by `pairId` | **Resolved 2026-10-14:** `GET /market/pairs` returns `pairId` (FEQ-01) | None: the web names every pair by the market list id |
| M-02 | CORS | TD 5.3: "CORS restricted to the configured web origins" | **Resolved 2026-10-04 (D-83, PR #50):** `common.config.CorsConfig` for REST and `/ws` (`backend/src/main/java/com/cryptopilot/common/config/CorsConfig.java#L34`) | None. Staging origins still need `CORS_ALLOWED_ORIGINS` (Q-07) |
| M-03 | Rate limits | TD 5.3: login 10/min/IP, API 120/min/user, AI 10/min/user | **Resolved 2026-10-04 (ADR-014, D-82):** `common.web.RateLimitFilter`, 429 `RATE_LIMITED` / MSG50 | Wait `Retry-After` seconds (03-conventions) |
| M-04 | Null fields in realtime payloads | TD 9 / D-51: "absent fields omitted" | No omit-null setting (`backend/src/main/java/com/cryptopilot/common/config/JacksonConfig.java#L39`); REST bodies carry `null` keys (`AnalysisControllerTest`), and the STOMP converter uses the same mapper (decimals arrive as strings in `MarketHubTest`), so ticker frames most likely carry `null` for the other market's fields. Not checked on a live frame | Treat missing and `null` alike |
| M-05 | Plan gates on market data and analysis | SRS 3.1.3, D-60: Futures analysis, Futures metrics, OI / long-short / settlement blocks and score components are PRO+ (MSG29) | Public / any Trader; no entitlement check (`backend/src/main/java/com/cryptopilot/market/controller/MarketController.java#L101`, `#L113`; `backend/src/main/java/com/cryptopilot/market/controller/AnalysisController.java#L50`). T-107 is READY, not built | Build the locks; expect 403 MSG29 after T-107 |
| M-06 | STOMP authentication and user queues | TD 9: bearer on CONNECT; `/user/queue/notifications`, `/positions`, `/ai` | Only the three public topic families; every other SUBSCRIBE refused (`backend/src/main/java/com/cryptopilot/common/config/WebSocketConfig.java#L55`) | None; planned |
| M-07 | Verification resend limit | SRS 3.2.2, D-57: once per 60 s, 5 per rolling 24 h, MSG46 | Always 202 (`backend/src/main/java/com/cryptopilot/auth/controller/AuthController.java#L105`); T-105 TODO | Client-side 60 s cooldown |
| M-08 | Watchlist row content | SRS 3.4.1: symbol, last price, 24h change, 1h setup score, active alerts | Row has symbol and active alerts, no price, change or score (`backend/src/main/java/com/cryptopilot/watchlist/dto/response/WatchlistItemResponse.java#L23`); D-75 records this choice | Prices from the overview topic; score per row from `GET /analysis` |
| M-09 | Futures last price and 24h statistics | SRS 3.3.1: Futures tab lists last price, 24h change, high, low, quote volume, plus mark price and funding; D-60 calls the Futures 24h ticker public | Futures stats and ticker topic carry only mark, index, funding rate, next funding time (`backend/src/main/java/com/cryptopilot/market/dto/response/FuturesStatsResponse.java#L22`, `backend/src/main/java/com/cryptopilot/market/dto/response/TickerUpdateResponse.java#L29`) | Show mark price in place of last price; leave 24h columns empty on Futures |
| M-10 | Plan list columns | SRS 3.5.2: pair, …, and for executed plans position status and P/L | Summary has `pairId` (no symbol) and no position fields (`backend/src/main/java/com/cryptopilot/trading/dto/response/TradingPlanSummaryResponse.java#L32`) | Resolve symbol from held data (FEQ-01); position fields wait for T-042+ |
| M-11 | Placeholders in field errors | SRS 5.3: MSG15 `{field} must be between {min} and {max}`, MSG16 `For {direction} positions: {rule}` | `errors` carries the code only; D-25's `messageArgs` covers business refusals, not field errors (`backend/src/main/java/com/cryptopilot/common/exception/GlobalExceptionHandler.java#L155`) | Client fills placeholders from its own labels and limits |
| M-12 | Futures plans | SRS 3.5.1: Futures plans with leverage 1 to the bracket maximum | Every Futures calculation fails: no leverage brackets are stored anywhere until T-085 (`backend/src/main/java/com/cryptopilot/trading/service/impl/PlanCalculationAssembler.java#L70`; D-70) | Disable Futures in SCR-17 for now or show the 400 |
| M-13 | Indicator overlays | SRS 3.3.2: overlays and panels over the chart | Latest values only (FEQ-04) | Client-side computation or wait |
| M-14 | Endpoint catalogue | TD 8 `user` row lists profile, notification preferences and devices only | Code also serves `GET/PUT /me/risk-profile` and `GET/POST /me/risk-questionnaire` (T-103) (`backend/src/main/java/com/cryptopilot/user/controller/RiskProfileController.java#L45`, `#L54`, `#L62`, `#L73`) | None needed; this guide documents them (`modules/user.md`) |
| M-15 | MSG50 | SRS v1.0 as submitted (Report 3, 3.7.4 and 5.3): MSG50 = "You have already reported this post." (BR-46). The `docs/srs/` copy (1.0 Draft) has no MSG50 | `RATE_LIMITED` answers MSG50 (`backend/src/main/java/com/cryptopilot/common/exception/ErrorCode.java#L223`; A-42) | Branch on `code`, not on `messageCode`, for 429 until Q-66 is answered |

## D. Checks done for this sync

- Every `Source:` path and line in this guide was checked against `develop` @ `0d92def` (154 line
  references; 12 had moved and were updated). First version: `6137e24`, alerts read on `0803903`.
- Every enum value and error code named here exists in code at those commits.
- Mermaid blocks were parsed with the Mermaid parser.
