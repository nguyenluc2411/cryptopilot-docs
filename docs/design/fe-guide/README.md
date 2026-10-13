# CryptoPilot — FE integration guide

For the web (React + TypeScript) and mobile (Flutter) engineers. It describes the backend API as it
exists in code, marks what is not built yet, and lists the gaps that need a decision.

| | |
|---|---|
| Synced to | `develop` @ `6137e2425cfe59a6c07ea84c2a86efe8a64a1e4f` (`6137e24`, merge of PR #42, 2026-10-02) |
| Pending branch read | `feat/t-054-alert-rules` @ `0803903` (alerts; not merged) |
| Sync date | 2026-10-03 |
| Backend | Java 21, Spring Boot 4.1, base path `/api/v1` |
| Spec | SRS v1.0 (`docs/srs/`), TECHNICAL_DESIGN (TD) sections 5, 8, 9, decisions D-xx in `CURRENT_STATE.md` |

## How to read this guide

1. `01-setup.md` — run the backend locally and point the client at it.
2. `02-auth.md` and `03-conventions.md` — every request depends on these two.
3. `04-enums.md` — the values every dropdown, badge and tab uses.
4. `05-realtime.md` — the STOMP market topics.
5. `modules/*.md` — one file per backend module, one section per endpoint.
6. `06-task-map.md` — your task (T-xxx) → screens → endpoints → what is ready.
7. `07-open-questions.md` — what is undecided or where spec and code disagree. Read it before
   building a screen it mentions.

## Status legend

| Status | Meaning | Can FE call it? |
|---|---|---|
| `IMPLEMENTED (develop)` | In code on `develop` at the SHA above | Yes |
| `PENDING PR (<branch>)` | In code on a branch that is not merged | No. Build against the contract, keep it behind a flag |
| `PLANNED (spec only)` | Only in TD 8 / SRS; no code | No. The shape will change |

## Files

| File | Content |
|---|---|
| [01-setup.md](01-setup.md) | Env vars, base URLs, CORS, local run |
| [02-auth.md](02-auth.md) | Tokens, login/refresh/logout, roles, plan gating |
| [03-conventions.md](03-conventions.md) | Error shape, error codes, MSG table, paging, dates, decimals |
| [04-enums.md](04-enums.md) | Every enum in a DTO, with suggested UI labels |
| [05-realtime.md](05-realtime.md) | STOMP endpoint, topics, payloads, reconnect |
| [modules/auth.md](modules/auth.md) | Register, verify, login, refresh, logout, reset, change password |
| [modules/user.md](modules/user.md) | Profile, notification preferences, risk profile, devices |
| [modules/market.md](modules/market.md) | Pairs, candles, stats, futures metrics, analysis |
| [modules/watchlist.md](modules/watchlist.md) | Watchlist and alerts |
| [modules/trading-plan.md](modules/trading-plan.md) | Trading plans |
| [modules/planned.md](modules/planned.md) | Journal, community, news, AI, billing, notifications, admin (spec only) |
| [06-task-map.md](06-task-map.md) | FE task → screens → endpoints → status |
| [07-open-questions.md](07-open-questions.md) | Open questions and spec-vs-code mismatches |
| [08-waiting-on-backend.md](08-waiting-on-backend.md) | What FE waits for from BE or the team lead, in priority order, and what FE does meanwhile |
| [CHANGELOG.md](CHANGELOG.md) | Changes to this guide |

## Endpoint count at this sync

| Status | REST | STOMP destinations |
|---|---|---|
| IMPLEMENTED (develop) | 35 | 3 topic families |
| PENDING PR (`feat/t-054-alert-rules`) | 6 new + 1 changed (`DELETE /watchlist/{id}`) | 0 |
| PLANNED (spec only) | 43 listed in TD 8 (42 in `modules/planned.md` + close-position) + 13 admin areas without methods | 3 user queues + analysis push (Q-21) |

## Where the rules come from

- Code wins over this guide. Each endpoint has a `Source:` line with the file and line at the SHA
  above. Code paths are relative to the repository root of `cryptopilot_project`.
- When code and spec disagree, this guide describes the code and records the difference in
  `07-open-questions.md`. It does not pick a side.
- The live OpenAPI document is at `GET /v3/api-docs` and Swagger UI at `/swagger-ui.html` when the
  backend runs with the `dev` profile (off in `prod`). Use it to check a field name quickly.

## Keeping it in sync

Re-sync after each backend PR that touches a controller, a DTO, `ErrorCode`, `SecurityConfig` or
`WebSocketConfig`. Update the SHA above, the affected module file, `06-task-map.md` and
`CHANGELOG.md`. Next expected re-sync: after the T-054 (alerts) and T-042 (matching engine) PRs merge.

## References

- Fielding, R. T. (2000). *Architectural Styles and the Design of Network-based Software
  Architectures*. PhD thesis, University of California, Irvine. (REST)
- Jones, M. & Hardt, D. (2012). RFC 6750, *The OAuth 2.0 Authorization Framework: Bearer Token
  Usage*. IETF. (bearer JWT on every protected request)
- Nottingham, M., Wilde, E. & Dalal, S. (2023). RFC 9457, *Problem Details for HTTP APIs*. IETF.
  (error body; the backend builds it with Spring's `ProblemDetail`)
- Fette, I. & Melnikov, A. (2011). RFC 6455, *The WebSocket Protocol*. IETF. (realtime transport
  under STOMP)
