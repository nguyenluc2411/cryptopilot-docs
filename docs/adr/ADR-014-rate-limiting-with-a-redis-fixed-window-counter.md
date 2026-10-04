# ADR-014 — Rate limiting with a Redis fixed-window counter in a servlet filter

**Status:** Accepted
**Date:** 2026-10-04
**Deciders:** BE1, BE2, FE, DO
**Related:** SRS 4.2.4, BR-03; TECHNICAL_DESIGN 1.3, 5.3, 5.6, 12; ADR-005; review finding R-06; CURRENT_STATE D-82, A-42

## Context
No endpoint is rate limited. BR-03 locks one account after five wrong passwords, but it does not slow a guess spread over many accounts, and each guess costs a bcrypt verification at cost 12. Registration, resend, forgot-password and reset are unthrottled per address. TECHNICAL_DESIGN 1.3 planned "Bucket4j (in-memory) in a servlet filter" with login 10/min/IP, API 120/min/user, AI 10/min/user (5.3), but nothing was built and Bucket4j is not on the classpath.

Constraints that decide the implementation:

- **Replicas.** The Docker deployment runs one backend instance on one VPS (ADR-005; staging is the same, TD 12). A second instance is not planned, but nothing should silently break if one is added.
- **Redis.** Already a dependency and always deployed next to the backend (`spring-boot-starter-data-redis`, `StringRedisTemplate`, Testcontainers Redis in the test suite). It holds no business data (ADR-005). Counters are operational state, not business data: losing them only resets the windows.
- **Per address vs per account.** The public auth endpoints are called before anyone is authenticated, so the only key is the client address, which is trustworthy only through the R-11 resolution (`X-Forwarded-For` honoured from configured proxies only). Authenticated API calls are keyed by the account (JWT subject), so one user behind a shared NAT does not starve another.
- **Endpoints covered.**
  - `POST /api/v1/auth/login`: per client address.
  - The other public `POST /api/v1/auth/**` endpoints (register, verify-email, resend-verification, refresh, logout, forgot-password, reset-password): per client address.
  - Every authenticated request under `/api/v1/**`: per account.
  - Not covered: the market data reads and the STOMP endpoint (public, cache backed, no per-request cost worth limiting yet); `/actuator/health`. The AI limit waits for the AI endpoints, which do not exist yet.
- **Testability.** The window must be testable without sleeping: the window is derived from the injected `Clock`.

## Decision
A `RateLimitFilter` in `common.web` runs after the Spring Security chain, so it sees the authenticated account. It counts requests in **fixed one-minute windows** in Redis. The key is `rl:{rule}:{subject}:{window}`, where `{subject}` is the R-11 client address or the account id, and `{window}` is the epoch minute from the injected clock. One Lua script does `INCR` and, on the first hit, `EXPIRE` for the window length, so a key never outlives its window. A request over the rule's limit is answered **429** with a `Retry-After` header (seconds to the end of the window) and the standard RFC 9457 problem body: `code` `RATE_LIMITED`, `messageCode` **MSG50**, `messageArgs` `[seconds]`. When Redis cannot be reached, the request is let through and the failure is logged and counted. The limiter must not turn a cache outage into a login outage (ADR-005: losing Redis costs a warm-up, not availability).

Limits (`cryptopilot.web.rate-limit.*`, per profile; environment overridable):

| Rule | Key | Limit per minute | Source |
|---|---|---|---|
| `login` | client address | 10 | TD 5.3 |
| `auth` | client address | 20 | new; covers refresh from several tabs behind one address |
| `api` | account | 120 | TD 5.3 |

The limiter is off without a profile (test contexts), on in `dev` (limits ×10 for local work) and in `prod` (the values above).

## Consequences
Positive: no new dependency; one small filter and one script; the counters survive a restart and are already shared if a second instance is ever added; the window is deterministic in tests (injected clock); the 429 uses the same problem format and the same `Retry-After` convention as the rest of the API.

Negative: a fixed window allows up to twice the limit across a window boundary; that is acceptable for these limits, and a sliding window can replace the script later without changing the filter's contract. Fail-open means an attacker who can take Redis down also removes the limit, so Redis stays on the private network only. One Redis round trip is added per limited request.

Requires: the trusted-proxy list (R-11) is set wherever a proxy sits in front, otherwise every client shares the proxy's address and its limit; MSG50 is added to SRS 5.3 (A-42).

## Alternatives considered
Bucket4j with its Redis (Lettuce) backend: rejected. It needs two new dependencies (`bucket4j-core`, `bucket4j-redis`) for token-bucket smoothing these limits do not need. The in-memory variant TD 1.3 planned would lose all counters on every restart and would not be shared across instances.
Nginx `limit_req`: rejected as the only mechanism. It can key only by address, not by account; its configuration is not in this repository (only `deploy/docker-compose.dev.yml` exists), so it cannot be tested by the backend suite; and it produces Nginx's own error page instead of the API's problem format and message code. It remains a reasonable outer layer for connection floods once `deploy/nginx/` exists.
Counting in a database table: rejected. One write per request on the transactional store, for state that can be lost without harm.
