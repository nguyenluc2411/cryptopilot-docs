# CURRENT_STATE.md — CryptoPilot Project State

**Last updated:** 2026-09-24 · **Document version:** 2.13 · **Phase:** P0 done bar the DO tasks; P1 done bar T-015 (PARTIAL, Q-12) and the web screens; P2 started
**Next task:** `T-018` — pair and coin model, pair filters (tick, step, min notional). T-019 needs it together with T-017; T-020 and T-023 are unblocked by T-017 as well, and T-016 by T-014.
T-017 is `DONE`: `market.client.BinanceRestClient` reads the public Spot and USD-M futures REST API — exchange
information, klines, premium index, funding rates, open interest and the long/short account ratio — with every
price parsed from the exchange's string straight to `BigDecimal`. Per venue it reads the used weight from every
response and pauses at 80% of the budget, waits out 429 and 418 for their `Retry-After` (418 logged as an alert),
retries 5xx and timeouts with back-off, and opens a circuit breaker after repeated failures (D-36, D-37). Every
Binance limit was verified against the official documentation and recorded with its source in TECHNICAL_DESIGN
7.1.1. **The WebSocket stream client was not built:** it is T-021 by the task list, not T-017. Branch
`feature/T-017-binance-market-data-client` (2 commits, cut from `origin/develop`, which does not contain T-014)
and `feature/T-014-profile-and-devices` (8 commits) are both local and **not pushed**. Still open from before:
T-015 `PARTIAL` (Q-12) and T-007 `PARTIAL` (Q-04, Q-05).

This file is the single source of truth for *status*. `docs/design/TECHNICAL_DESIGN.md` owns *how*; the SRS owns *what*. Every working session starts by reading this file and ends by updating it (`CLAUDE.md` sections 1 and 8).

---

## 1. How to use this file

**Human team:** update the Status column after each stand-up. Move `NEXT` only when a task's dependencies are `DONE`.

**First time on a new clone (human):** run `sh docs/tools/setup-local.sh` (Windows: `powershell -ExecutionPolicy Bypass -File docs\tools\setup-local.ps1`). It keeps this file and the other local documents out of git and installs the commit hooks. Then `git status --short` must not list any of them.

**AI agent, every session** (shortcut: `/start-task`, then `/end-session`):
1. Read section 3 (Progress) → find the task marked `NEXT` in section 6.
2. Read that task's row plus its detail block in section 7 (if present).
3. Read section 4 (Decisions), section 5 (SRS Alignment) and section 8 (Open Questions) — these override the SRS where marked `APPROVED`.
4. Do the mandatory codebase analysis (`CLAUDE.md` section 2).
5. Implement, test, then append a session block to section 9 and update the status of the task and the `NEXT` marker.

**Status values:** `TODO` · `NEXT` · `WIP` · `PARTIAL` (merged but incomplete, has an open question) · `BLOCKED` · `DONE` · `DROPPED`.

A task may be marked `DONE` only when the Definition of Done in `CLAUDE.md` section 6 is satisfied. Never mark `DONE` with failing tests.

---

## 2. Project facts

| Item | Value |
|---|---|
| Product | CryptoPilot — Crypto Trading Support System (decision support + paper trading) |
| Period | 09/2026 → 03/2027 (26 weeks, 13 sprints of 2 weeks) |
| Sprint 0 starts | 2026-09-22 |
| Supervisor | Nguyễn Ngọc Lâm (lamnn15@fpt.edu.vn) |
| Team | BE1 backend lead · BE2 backend · FE frontend/mobile · DO devops |
| Architecture | Modular monolith (Java 21 + Spring Boot 4.1) + stateless AI Service (Node.js) — ADR-001, ADR-002 |
| Repository | `cryptopilot/` — structure in TECHNICAL_DESIGN section 4 |
| Branching | `main` ← `develop` ← `feature/T-xxx-short-name` |
| Local-only files | `CLAUDE.md`, `CURRENT_STATE.md`, `.claude/`, `docs/` — never committed (D-15) |

**Hard scope boundary (never violate):** no real order execution, no exchange API keys, no custody of funds, no investment advice.

---

## 3. Progress

| Phase | Sprint | Scope | Tasks | Done | Status |
|---|---|---|---|---|---|
| P0 Foundation | S0 | Repo, CI, database, docker, architecture tests | 9 | 5 | WIP — T-007 PARTIAL |
| P1 Identity | S1 | Register, verify, login, tokens, profile, devices | 8 | 6 | WIP — T-015 PARTIAL, T-016 TODO (unblocked) |
| P2 Market Data | S2 | Pairs, backfill, streams, futures metrics | 8 | 1 | WIP — T-017 DONE, T-018 NEXT |
| P3 Analysis | S2–S3 | Indicators, S/R, setup score | 5 | 0 | TODO |
| P4 Market UI | S3 | Public home, market list, spot/futures analysis | 5 | 0 | TODO |
| P5 Trading Plan | S3–S4 | Risk calculation, warnings, plan lifecycle | 7 | 0 | TODO |
| P6 Matching | S4–S5 | Simulated fills, exits, liquidation, funding | 6 | 0 | TODO |
| P7 Journal | S5 | Journal, manual trades, performance dashboard | 5 | 0 | TODO |
| P8 Monitoring | S6 | Watchlist, alerts, alert engine, notifications | 7 | 0 | TODO |
| P9 Community | S7 | Posts, media, comments, engagement, reports | 7 | 0 | TODO |
| P10 Billing | S8 | Packages, orders, VNPay/MoMo, subscriptions | 6 | 0 | TODO |
| P11 AI Assistant | S9 | AI Service, conversations, quota | 5 | 0 | TODO |
| P12 News | S9 | Sources, crawl, dedup, tagging, summary | 4 | 0 | TODO |
| P13 Administration | S10 | Users, moderation, config, reports, audit | 7 | 0 | TODO |
| P14 Mobile | S11 | Flutter app, push, offline | 5 | 0 | TODO |
| P15 Hardening | S12 | E2E, performance, security, deploy, docs | 7 | 0 | TODO |
| **Total** | | | **101** | **12** | **12%** |

**Coverage:** `calculator` packages — no class yet (gate 90%) · Backend on the T-017 branch 98.65% line (952/965), branches 95.31% (244/256) (gate 70%); on the T-014 branch 98.42% / 95.98% · AI Service —% (gate 80%). The two branches have not been merged together yet, so there is no single figure.
**Test suite:** T-017 branch 747/747 (`./mvnw clean verify`): the 705 of `develop` plus 42 for the Binance client (37 REST client against a local stand-in server, 4 request gate, 1 candle close). T-014 branch 792/792. Two tests tagged `live` call the real exchange and are excluded from the default build (`-Dgroups=live -Dsurefire.excludedGroups=none` runs them; they passed once on 2026-09-24). The suite needs Docker running (Testcontainers) and a signing key (`JWT_SECRET`, supplied by Surefire, D-20).

> The figure before T-015 was recorded here as 578; the measured baseline was **576** — the "148 shared kernel" was 146. T-015 added 98 tests (80 + 11 + 7 in `ErrorCodeTest` from the two new codes), so 576 + 98 = 674.
**Merged to `develop`:** everything built so far. `develop` is at `428e66d` (`5311036` plus one docs commit) after a **fast-forward** of the whole
line of work — T-002, T-003, T-005, T-008 (pull requests #1 and #2) plus T-006, T-007, T-010, T-011, T-012, T-015,
T-100 and T-013, 41 commits. It was merged and reviewed by the agent at the team's instruction, **not by a second
person**, and that is the weaker of the two: the automated review was rate-limited before it read anything, so what
stands behind this merge is the suite (705/705), the pre-merge hygiene scan and a self-review, which found A-29.
A human pass over `develop..14fe422` is still worth doing. Fast-forward was chosen over a merge commit because
`develop` was strictly behind, so the history is linear and no commit names the branch it arrived on. `main` is
untouched.
**Not merged:** `feature/T-014-profile-and-devices`, 8 commits on top of `develop` (`9972550` … `16db72c`), **pushed and open as PR #3 into `develop`** (2026-09-24, awaiting the team lead's review), and `feature/T-017-binance-market-data-client`, 2 commits on top of `develop` (`43bb438`, `0d0ee0b`); both local only. They touch different modules and should merge without conflict; `pom.xml` and `application.yml` are the only files T-017 shares with anything.
**Deployed:** dev — · staging —

### Critical path
`P0 → P1 → P2 → P3 → P5 → P6 → P7 → P14 → P15`
P8, P9, P10, P12, P13 can run in parallel once P1 and P2 are `DONE`. P11 depends on P3 (context snapshot) and P10 (entitlement).

### Capacity notes
- S9 (26/01 – 08/02/2027) overlaps the Tết holiday. Plan ~50% capacity; do not place critical-path work there — P11 and P12 are parallel work by design.
- S12 is the last sprint: feature freeze at its start, only fixes, documentation and the demo after that.

---

## 4. Decisions

Decisions that bind the code. An AI agent must follow `APPROVED` rows and must not contradict them.

| ID | Date | Decision | Status | Source |
|---|---|---|---|---|
| D-01 | 2026-09-11 | Modular monolith + separate AI Service instead of microservices | APPROVED | ADR-001 |
| D-02 | 2026-09-19 | Backend runs on Java 21 LTS with Spring Boot 4.1.x, built with Maven and the committed wrapper (Boot 3.5 is out of OSS support, 4.0 ends mid-project) | APPROVED | ADR-002 |
| D-03 | 2026-09-19 | Package by module, then by layer; boundaries verified by Spring Modulith and ArchUnit | APPROVED | ADR-003 |
| D-04 | 2026-09-19 | AI Service is stateless; the backend is the only database writer | PROPOSED | ADR-004 |
| D-05 | 2026-09-19 | No MediatR / AutoMapper / FluentAssertions v8+; explicit handlers, manual mapping, Shouldly | PROPOSED | ADR-007 |
| D-06 | 2026-09-19 | Money, prices and quantities use `decimal` only; `double` is allowed for indicator maths only | PROPOSED | ADR-008 |
| D-07 | 2026-09-19 | UUID v7 primary keys generated by the application | PROPOSED | ADR-009 |
| D-08 | 2026-09-19 | Transactional outbox for notifications, email, push and AI requests | PROPOSED | ADR-010 |
| D-09 | 2026-09-19 | Matching engine reads the `kline_1m` stream (high/low) plus the mark price stream | PROPOSED | ADR-011 |
| D-10 | 2026-09-18 | Futures plans support isolated margin only | APPROVED | SRS BR-26 |
| D-11 | 2026-09-18 | One take profit per plan; no partial closing in v1 | APPROVED | SRS 5.4.1 |
| D-12 | 2026-09-18 | Simulated P/L includes trading fees and funding | APPROVED | SRS BR-36, BR-37 |
| D-13 | 2026-09-18 | An alert always belongs to a watched pair; the pair is added automatically | APPROVED | SRS BR-16 |
| D-14 | 2026-09-18 | Forum content uses soft delete; only posts can be reported (not comments) | APPROVED | SRS BR-47 |
| D-15 | 2026-09-19 | Project documents and AI tooling stay local (`.git/info/exclude`); commits, PRs, code and comments carry no AI attribution; enforced by local `pre-commit` and `commit-msg` hooks | APPROVED | Team lead |
| D-18 | 2026-09-20 | Database stack: PostgreSQL 16 + TimescaleDB 2.x, Docker image `timescale/timescaledb:2.30.1-pg16` pinned everywhere (dev compose, Testcontainers, staging); schema owned by Flyway SQL migrations with the TimescaleDB DDL in its own migration; staging is self-hosted Docker on a VPS, never a managed PostgreSQL | APPROVED | Team lead; TECHNICAL_DESIGN section 6 |
| D-19 | 2026-09-21 | Reference and bootstrap data is a versioned Flyway migration (`V3__seed_reference_data.sql`), not a runtime seeder: it is checksummed, applied once, and reviewed with the schema it depends on. Sample data is a **repeatable** migration in a separate location (`classpath:db/demo`) that only the `dev` profile adds to `spring.flyway.locations`, so production cannot reach it at all. Seeded primary keys are fixed uuid v7 literals (generation happens in the application and would differ per database); every seeded instant is the fixed constant `2026-01-01T00:00:00Z`, never `now()`; every insert carries `ON CONFLICT (<primary key>) DO NOTHING`, and a collision on any other unique key is left to raise | PROPOSED | T-007 |
| D-23 | 2026-09-21 | Repository shape: one repository per aggregate root, extending `Repository<T, ID>` rather than `JpaRepository`, so that `findAll`, `count` and `deleteAll` are never contributed to a table that grows with users — an unbounded read has to be written deliberately, and a paged one is what the listing screens will add. Reads declare `@Transactional(readOnly = true)`; `save` declares nothing, so the unit of work is the calling service's. A case-insensitive lookup is explicit JPQL over `lower(...)`, never the derived `IgnoreCase` keyword, because the schema's functional index is on `lower(email)` while the keyword generates `upper(...)` | PROPOSED | T-011 |
| D-24 | 2026-09-21 | Profile write path: `UserProfileRepository`, a repository for something that is not an aggregate root. The three options were weighed against D-21 and D-23 and this is the only one that bends a rule the design can afford to bend. **Rejected:** a cascading `@OneToOne` from the account, because reversing D-21 for one association turns "no JPA association" from a rule into a convention and brings a fetch decision with it; persisting through the `EntityManager` in the service, because it keeps both rules intact but puts two persistence idioms in one class, and T-014 has to *load* the profile to edit it, so the manager would spread rather than stay in one method. **The cost, stated:** "one repository per aggregate root" (D-23) now has one documented exception. It is safe only because it is forced — with no association there is no way to navigate to the row, so a row with its own table and its own key needs its own gateway or it cannot be reached at all. The rule still holds for anything reachable through its root. **For T-014:** the profile edit screen already has its gateway and needs no new one | PROPOSED | T-011 |
| D-21 | 2026-09-21 | Identity mapping: no JPA association anywhere in the identity tables. A profile is keyed by the account it describes, a device and a token name it with a plain `UUID`. Across a module boundary this is forced — `auth` may not map `user`'s entity — and inside `user` it is chosen, because nothing navigates one yet and an association decides a fetch strategy, adds a second way to load a row and becomes an N+1 the moment somebody makes it eager. Two tests guard the absence: no entity holds an association, and reading many rows costs one statement. An association may be added later with a reason, a fetch type and a test that states its cost | PROPOSED | T-010 |
| D-22 | 2026-09-21 | `created_at` and `updated_at` are written by one Spring-managed JPA entity listener from the injected `Clock`, never by a database default and never by `Instant.now()` inside an entity. A test that needs a known instant replaces the one clock bean | PROPOSED | T-010 |
| D-20 | 2026-09-21 | No credential of any kind in a committed file. The bootstrap administrator's password hash reaches the database as the Flyway placeholder `${admin_password_hash}`, supplied already hashed from `ADMIN_PASSWORD_HASH`; when the environment supplies nothing it falls back to `!ADMIN_PASSWORD_HASH_NOT_SET`, which is not a hash in any format an encoder produces, so the account exists but no password opens it. The address is `admin@cryptopilot.invalid` (RFC 2606), which can never resolve or belong to a person. `DEMO_PASSWORD_HASH` works the same way for the demo trader | PROPOSED | T-007 |
| D-25 | 2026-09-21 | Message arguments on `BusinessException`: a rejection carries the values its SRS message leaves a hole for — MSG09's minutes, MSG10's status — positional, rendered as text, and returned as a `messageArgs` property on the RFC 9457 problem detail. **Rejected:** the backend formatting the finished sentence, because that puts a copy of SRS section 5.3 in two repositories and makes the client's language the server's business; a named map instead of a position, because a message code plus a position is already a contract and a second one would have to be kept in step with it; a field per message, because every later message with a placeholder would change the response shape for every client. **The cost, stated:** the client now has to know the order of the placeholders of each message code, so SRS 5.3 is load-bearing at the level of the sentence for MSG09 and MSG10 — reordering the placeholders of a message breaks its display with nothing failing. An argument is always a value and never a secret, because it is returned in the body | PROPOSED | T-012 |
| D-26 | 2026-09-21 | "Remember me" survives rotation without a column: the successor of a refresh token is given thirty days when the retired token's own window was longer than the ordinary seven, and seven otherwise, so a remembered session stays remembered through any number of renewals. **Rejected:** a `remember_me` column on `user_token`, because it is a fourth column on a table A-10 has just widened and it would store something the row already says; carrying the flag in the refresh request, because the client would then be choosing its own session length after the sign-in decided it; letting every successor fall back to seven days, because a thirty-day sign-in would quietly become a seven-day one at the first renewal and nothing would report it. **The cost, stated:** the rule is a comparison of two windows, so it is sound only while they stay far apart — seven days and thirty. A later configuration that puts them close together, or that makes the remembered window the shorter one, reads the wrong answer and forces the column after all. `TokenProperties.refreshTokenTtl(boolean)` is the single place both windows are decided, so that is where such a change would be noticed | PROPOSED | T-012 |

| D-27 | 2026-09-21 | The role half of SRS 3.1.3 is enforced by the security filter chain as path rules, not by `@PreAuthorize` on controllers. TECHNICAL_DESIGN 5.3 said `@PreAuthorize`; this supersedes that sentence and 5.3 now records the split. Three reasons, in order of weight: the chain already ends in `anyRequest().denyAll()`, so a path must be named there to be reachable at all and an annotation could not open one — the chain is doing the work either way; "Guest" is a column of the matrix and no method annotation can express it, because an anonymous request has no method to annotate; and an area rule (`/api/v1/plans/**` is TRADER) covers endpoints that do not exist yet, so a controller added in a later sprint inherits the right rule instead of waiting for somebody to remember an annotation. **Rejected:** annotations per controller, because forgetting one leaves the endpoint unreachable and the fix under time pressure is to widen the chain, which is the failure this arrangement is meant to prevent; a mixed scheme with roles in both places, because two sources for one answer is the drift the matrix cannot afford. **The cost, stated:** a rule names a path, so a path that is renamed or misspelled silently stops matching and falls to `denyAll`. That fails closed and the owning task's own tests catch it, but it does mean the chain has to be read together with TECHNICAL_DESIGN 8 whenever the catalogue changes. `@PreAuthorize` stays for entitlement, which is not a property of a path; ownership stays in services | PROPOSED | T-015 |
| D-28 | 2026-09-21 | `CorrelationIdFilter` is registered at `Ordered.HIGHEST_PRECEDENCE`, ahead of Spring Security's chain (order −100). Until T-015 it had no order and therefore sat behind it, so every request the chain refused — every 401 and every 403 — ran no correlation filter: no id in the logging context, no `traceId` in the body and no `X-Correlation-Id` on the response. Those are precisely the responses somebody asks about afterwards. Nothing in the filter reads the caller's identity, so being ahead of authentication costs nothing | PROPOSED | T-015 |
| D-29 | 2026-09-23 | Lombok is used in exactly two places and made unable to reach any other: `@Getter` on an entity class, and `@RequiredArgsConstructor(access = AccessLevel.PACKAGE)` on a bean whose constructor does nothing but assign its collaborators. `backend/lombok.config` turns `@Setter`, `@Data`, `@EqualsAndHashCode` and `@ToString` into compile errors, so TD 1.3's prohibition stops being a sentence somebody has to remember, and sets `addLombokGeneratedAnnotation` so a generated member cannot move the JaCoCo ratio in either direction. **Rejected:** `@NoArgsConstructor(access = PROTECTED)`, which TD 3.4 permits — it is longer than the `protected UserAccount() {}` it would replace and it hides a JPA requirement behind an annotation, so it buys nothing; `@RequiredArgsConstructor` at its default public access, because five of these constructors are deliberately package-private and widening them to save a keyword is the wrong trade; `@Getter` on the four accessors that compute something (`isNew`, `isEmailVerified`, `isLockedOutAt`, `isUsableAt`), which are behaviour wearing a getter's name. **The cost, stated:** two classes keep hand-written constructors because theirs do work beyond assignment — `AuthService` derives `hashOfNothing` and `JwtConfig` derives the signing key — so "every bean uses the annotation" is not true and a reader has to see why. The annotation is only correct while a constructor stays a pure assignment; the moment one needs a line of logic it goes back to being written out, and that is a normal edit rather than a violation | PROPOSED | T-100 |
| D-30 | 2026-09-23 | A rule that both a request record and a service must read lives in the module's root package, not in either layer. `PasswordPolicy` moved from `auth.service` to `auth` because `RegisterRequest` has to declare BR-02 as a bean-validation pattern and a `dto` may not depend on a `service`. **The reason it was never caught:** `PATTERN` is a constant variable, so javac copies its value into the annotation and leaves no reference in the bytecode — ArchUnit reads bytecode, so `LayerRulesTest` passed 9/9 with the violation present, which the T-100 baseline of 674/674 proves. A rule that can only be broken invisibly is not enforced. `LayerSourceRulesTest` now states the same table over the import lines, and it was verified against a probe that reads only a constant: ArchUnit passed it, the source test refused it. **Rejected:** duplicating the expression in the request record, because the class exists to hold BR-02 once; moving it to `common`, which carries no business logic. **The cost, stated:** `PasswordPolicy` is now part of the `auth` module's public surface, and one layer table is stated in two files that can drift. The source test covers only the pairs inside `com.cryptopilot`; framework rules stay with ArchUnit, where the bytecode is the honest source | PROPOSED | T-100 |
| D-31 | 2026-09-23 | One factory makes every opaque token. `VerificationTokenFactory` and `RefreshTokenFactory` were identical from the package statement to the closing brace - same 256 bits, same generator, same URL-safe encoding, same SHA-256 digest - and differed only in the visibility of one constant. T-013 would have been the third copy. They are now `SecureTokenFactory`, and what actually differs between the three kinds of token - how long one lasts, what presenting it achieves, which rule retires it - lives on `UserToken` and in the use case, where it always did. **Rejected:** a third class for the reset link, which is the duplication the rule about reusing abstractions exists to stop; keeping the two and letting the reset link borrow the verification one, because the name would then be a lie at two of the three call sites. **The cost, stated:** a rename reaching T-011's and T-012's code, which is refactoring their files inside another task's commit. It is accepted because the alternative was to add to the duplication rather than to leave it alone - there was no option that touched nothing | PROPOSED | T-013 |
| D-32 | 2026-09-23 | UC-04 is two methods on `AuthService`, not a `PasswordResetService` as TD 4.1 listed. The two halves share the token table, the single-use rule, the digest-only handling, the non-enumeration shape of the resend and the bulk revocation of logout; a separate class would have to reach every one of them and would own none. **Rejected:** a class per use case, which would put the four token lifecycles in four places that all write one table. **The cost, stated:** `AuthService` is now 600 lines and holds UC-01 to UC-05. That is the cost of the seam being the table rather than the use case, and it is the right moment to split when a second table appears - the mail module of A-18, or UC-07's change-password, which needs the current password and therefore a session. Splitting it now would be splitting on names | PROPOSED | T-013 |
| D-33 | 2026-09-24 | Every access token carries a `sid` claim: the family id of the refresh token issued beside it. SRS 3.2.5 says a password change revokes all **other** sessions, and an access token that names only an account cannot say which session is "this one". The claim grants nothing and identifies a sign-in, not a person; the name is OpenID Connect's for a session identifier. A token without it (issued before T-014) is read as naming no session, and then every session is revoked — the stronger reading of the rule, costing the caller one sign-in. **Rejected:** sending the refresh token in the password-change body, because it puts the one long-lived credential into a second endpoint; revoking every session including the caller's and issuing a new pair in the response, because it contradicts "other" and turns a password change into a sign-in. **Extended in the T-014 follow-up:** the claim is also checked on every request — `SessionLivenessValidator` refuses a token whose family holds no unused refresh token, through `LiveSessions`, an in-memory answer cache of at most one minute evicted per account after the commit of every path that ends sessions. **Rejected:** a query per request with no cache, which puts a database read in front of every endpoint; Redis, which is not a dependency yet and would be the only reason to add it now. **The cost, stated:** one more claim in a token every request carries; rotation must keep the family, which it already does (TD 7.15); every future path that ends sessions (BR-06 in T-083) must evict, or its sessions live on for up to a minute; and the cache is per process, so a second instance needs the shared cache | PROPOSED | T-014 |
| D-34 | 2026-09-24 | Device tokens. A token is unique across accounts, so registering one decides by who holds it: nobody → a new row; the caller → the same row reactivated and seen now; another account → the row becomes a new device of the caller's (new key, new creation instant). **Since the T-014 follow-up all three cases are one statement,** `INSERT ... ON CONFLICT (fcm_token) DO UPDATE` over `uq_user_device_fcm_token`, because the read-then-delete-then-insert it replaced failed two registrations arriving together (unique violation, or a delete of a row already gone) — `DeviceRegistrationConcurrencyTest` failed on the old code and passes on the new. Deactivation is by device key from the signed-in app (`DELETE /me/devices/{id}`, never the token in a URL) and by token from `POST /auth/logout`, whose optional `fcmToken` is deactivated only if it belongs to the account the refresh token belongs to. **Rejected:** moving the row to the new account, which would hand one account's device history to another; relying on the app calling `DELETE` before logout alone, because an app whose access token has expired would have to refresh first just to be silenced. **The cost, stated:** two ways to deactivate, and the logout body is now wider than the refresh body (`LogoutRequest` vs `RefreshRequest`) | PROPOSED | T-014 |
| D-35 | 2026-09-24 | A wrong current password on the Security tab is its own error code, `CURRENT_PASSWORD_INCORRECT`, 400 with MSG08 — not `INVALID_CREDENTIALS`, which is 401. A 401 on a request that carried a valid access token tells a client its session is over and would send somebody who mistyped back to SCR-04. Same message, different status | PROPOSED | T-014 |
| D-36 | 2026-09-24 | The Binance client is tested against a local stand-in built on the JDK's `com.sun.net.httpserver`, not WireMock. The task row and TECHNICAL_DESIGN 11.1 name WireMock, but it is not in `pom.xml`, and every case T-017 needs — a status, headers, a body, a delay, a count of requests — is thirty lines on the JDK server. **Rejected:** adding WireMock now, a dependency for canned answers; `MockRestServiceServer`, because it replaces the HTTP layer and so cannot produce a real read timeout or a refused connection. **The cost, stated:** a small test helper (`StubExchange`) to maintain; the payment adapters (T-067, T-068) may still want WireMock for signature fixtures, and that is the moment to decide again | PROPOSED | T-017 |
| D-37 | 2026-09-24 | Resilience of the Binance client is built from what the stack already has: Spring Framework 7 `RetryTemplate` for transient failures, and a circuit breaker of about thirty lines in `BinanceRequestGate` (consecutive failed calls open it for a fixed time, then one trial call). TECHNICAL_DESIGN 1.3 left the breaker to T-017 "after checking Spring Boot 4 compatibility"; Resilience4j's Boot 4 support was not confirmed, and the breaker needed here is small. The same gate enforces the weight budget and the 429/418 waits per venue, and it **refuses** rather than sleeps: a refusal carries the instant to retry at, and the job that called decides. **The cost, stated:** a breaker the project owns and tests itself; if a second integration (AI Service, payment) needs one, move to Resilience4j then rather than copy this one | PROPOSED | T-017 |
**Action:** D-02 and D-03 were confirmed by the team on 2026-09-19 and are `APPROVED`; D-18 on 2026-09-20. D-04 … D-09 still need confirmation; D-06 and D-07 are already load-bearing in committed code (T-008). D-19 and D-20 are load-bearing as of T-007 and need confirmation before the first staging deployment, because D-20 decides how an operator obtains the first administrator. D-21 and D-22 are load-bearing as of T-010; D-21 is the one worth arguing about, because reversing it later means touching every entity that was written under it. D-29 and D-30 are load-bearing as of T-100; D-31 and D-32 as of T-013. D-23 … D-26 are load-bearing as of T-011 and T-012; D-26 is the one to re-read if the refresh windows of SRS 3.2.3 are ever changed, because it infers "Remember me" from the length of the window rather than from a stored flag.

---

## 5. SRS alignment items

Deviations found while designing. Each needs team approval, then the SRS and the logical model are updated in the same session and the row moves to `APPROVED`.

| ID | Item | Proposal | Affects | Status | Blocks |
|---|---|---|---|---|---|
| A-01 | BR-27 ignores the maintenance amount of the bracket | Use the exact formula with `cum` (TD 7.6) | BR-27 | PENDING | T-036 |
| A-02 | BR-35 "loss equals initial margin" conflicts with fees in BR-36 | Price loss = initial margin; fees and funding added separately | BR-35 | PENDING | T-044 |
| A-03 | BR-53 requires PENDING, but the gateway can confirm after expiry | Accept a late success, activate, write an audit entry | BR-53, BR-54 | PENDING | T-069 |
| A-04 | NSF-07 recovery uses 15m candles | Replay 1m klines fetched by REST | SRS 3.5.4 | PENDING | T-043 |
| A-05 | NSF-08 applies funding at each funding time | Compute from `funding_rate_history` rows on close/read; identical result (the rows the settlements moved to under A-12) | NSF-08 | PENDING | T-045 |
| A-06 | NSF-16 says the AI Service stores the answer | AI Service stateless; the backend persists | NSF-16, SRS 4.1.3 | PENDING | T-073 |
| A-07 | Setup score has no direction | Two-direction score plus a `setup_bias` column on `technical_indicator` | BR-13, logical model | PENDING | T-026 |
| A-08 | Backend runtime named in the SRS | The SRS stays technology-neutral; the runtime (Java 21 + Spring Boot 4.1) is recorded in ADR-002 only, so no SRS change is needed | — | RESOLVED 2026-09-19 | — |
| A-10 | The logical model has no columns for two rules the design already states: BR-03 needs a failed login counter and a lock instant on `user_account`, and the refresh token rotation of TECHNICAL_DESIGN 7.15 needs a family id on `user_token` | Add `failed_login_count`, `locked_until` to `user_account` and `token_family_id` to `user_token` in an additive migration inside T-012 | BR-03, BR-04, logical model | RESOLVED 2026-09-21 — `V4__login_lockout_and_refresh_family.sql` adds all three plus `ck_user_account_failed_login_count` and `idx_user_token_family`; `V5__refresh_token_family_invariant.sql` adds `ck_user_token_family`, which states that exactly the refresh tokens carry a family, once the mapping upholds it. **The logical model still has to gain the three columns** — the schema is ahead of the document until somebody edits it | — |
| A-09 | Physical technical tables absent from the ERD | `event_publication` (Spring Modulith registry) and `flyway_schema_history` are technical tables, not business entities; documented as such, outside the ERD | SRS 3.1.5 | APPROVED 2026-09-20 | — |
| A-11 | `version`, `created_at` and `updated_at` are not in the logical model, but every entity table needs them: optimistic locking (TECHNICAL_DESIGN 5.5) and the audit instants `BaseEntity` writes from the injected clock | Technical columns `version`, `created_at`, `updated_at` exist in the physical model only; they are not business attributes, so the ERD stays unchanged and no SRS text moves | SRS 3.1.5, logical model | APPROVED 2026-09-20 | — |
| A-17 | SRS section 5.3 has no message for a write refused because it would duplicate an existing record, other than the address-specific MSG04. A lost race on any other unique constraint therefore has no text to show | Add a generic conflict message (MSG47), or accept that every constraint a use case can collide with must name its own message. Until then `ErrorCode.DATA_CONFLICT` borrows the reference-code text of MSG43 with a 409 status, which is recorded in the code | SRS 5.3 | PENDING | — |
| A-15 | SRS section 5.3 has no error message for an administrator's account status change that is refused — unlocking an account that is not locked, or any action on a banned one. MSG39 is the only message about an administrator changing an account status and it is written as a confirmation prompt, not a refusal | Add a message for the refusal (MSG46), or give MSG39 an error variant. Until then `ErrorCode.ACCOUNT_STATUS_TRANSITION_INVALID` names MSG39 as the nearest existing message, which is recorded in the code | SRS 5.3, BR-05 | PENDING | — |
| A-16 | The SRS describes the administration actions as Lock, Unlock, Ban and Change Role, and names no Unban. The entity therefore treats BANNED as terminal, which the SRS states only by omission | Say in BR-05 or BR-06 that a ban is permanent and that an account is never returned from it, so the absence of an Unban action is a decision rather than a gap | BR-05, BR-06 | PENDING | — |
| A-13 | The logical model's example settings keys (`MAX_ALERTS_PER_USER`, `MAX_UPLOAD_MB`) do not match the SRS. BR-17 names the limit `MAX_ACTIVE_ALERTS`, and BR-44 states four separate media limits rather than one upload size | The seed uses the SRS names (`MAX_ACTIVE_ALERTS`) and splits the upload limit into `MAX_IMAGES_PER_POST`, `MAX_IMAGE_SIZE_MB`, `MAX_VIDEO_SIZE_MB`, `MAX_VIDEO_DURATION_SECONDS`, because the SRS outranks the logical model (TECHNICAL_DESIGN section 0). The logical model's example list is updated to match | BR-17, BR-44, logical model | PENDING | — |
| A-14 | BR-05 lets only an Admin assign the ADMIN role and makes every self-registered account a TRADER, so the SRS describes no way for the first Admin to come into existence | The first Admin is seeded with the schema, with no usable credential until an operator supplies one (D-20). The SRS gains one sentence in BR-05 stating that the initial administrator is provisioned with the system rather than registered | BR-05 | PENDING | — |
| A-18 | `VerificationTokenIssued` carries the raw verification link, because a link cannot be rebuilt from the digest the database stores. **T-013 adds a second one, `PasswordResetTokenIssued`, with the same property and a worse consequence: presenting one of those sets a password.** That is safe only while the event stays in memory. The moment the Spring Modulith event publication registry of ADR-010 is switched on, the value is written to `event_publication.serialized_event` in the clear and survives there until completed rows are swept — which defeats the point of storing only a digest | Decide before the registry lands: either the event carries an opaque reference the mail module exchanges for the link, or the registry's completed rows are swept on a schedule short enough that a leaked table is not a set of working links. Not decidable inside T-011, because no notification module exists to shape the seam | BR-01, BR-04, SRS 4.2.4, ADR-010 | PENDING | T-011's successor that adds the mail module |
| A-19 | A superseded verification token and a redeemed one are indistinguishable afterwards. SRS 3.2.2 requires a new link to invalidate the previous unused ones, and `used_at` is the only column the schema has for "no longer usable", so supersession is recorded there | Confirm that nothing later needs to tell the two apart — an audit of how a link was retired, or a metric counting redemptions, would need a separate column or a status. Nothing in BR-01 or UC-02 depends on it today | SRS 3.2.2, logical model | PENDING | — |
| A-20 | SRS 3.2.1 requires the password and its confirmation to match, and section 5.3 has no message for a mismatch. The request record reports it under `confirmPassword` with MSG03, the code of the password rule it belongs to, which is the nearest existing message rather than the right one. **SCR-06 asks for the same confirmation (SRS 3.2.4) and `ResetPasswordRequest` reports it the same way, so the borrowed code is now on two screens.** | Add a message for the mismatch, or state in 3.2.1 that MSG03 covers it and that 3.2.4 inherits it | SRS 5.3, 3.2.1, 3.2.4 | PENDING | — |
| A-21 | SRS 3.2.2 caps verification resends at five per day and fixes no boundary for the day. The implementation counts from 00:00 UTC+7, borrowed from BR-50's daily AI quota, because the alternative was inventing a second convention for the same word | Confirm that every daily limit in the system resets at 00:00 UTC+7, and say so once in the SRS rather than per rule. If the answer differs, the resend cap follows it | SRS 3.2.2, BR-50 | PENDING | — |
| A-22 | BR-03 says an account is locked for fifteen minutes after five *consecutive* failures and says nothing about the counter once those fifteen minutes have been served. Carrying the old count forward would make the next single mistake lock the account again, which turns a fifteen-minute penalty into a permanent one for anybody who mistypes twice in an evening and makes the rule's own word "consecutive" untrue | The lockout is treated as ending the run: a served lockout is cleared by the next attempt and the counter restarts at one, which is what `UserAccount.recordFailedLogin` does and what its tests pin. Confirm that reading, or state the intended behaviour in BR-03 | BR-03 | PENDING | — |
| A-23 | SRS 3.1.3 authorizes **screens**, and the filter chain authorizes **paths**. The two are not one to one, and one row splits: SCR-01 Public Home shows "realtime prices, 24h statistics and a basic price chart" to a Guest, while SCR-10 and SCR-11 place the *same pair's* analysis inside the Trader area. There is no row that says which endpoint each half is | Read as: `GET /api/v1/market/**` (pairs, candles, statistics, futures metrics) is public, because that is the data SCR-01 draws and the matrix has a "Query Public Data (market overview)" row with Guest marked; `/api/v1/analysis/**` (indicators, support/resistance, setup score) is TRADER, because it is the computed part that SCR-10 and SCR-11 add. Confirm both halves, and in particular whether the futures metrics of SCR-11 - funding rate, open interest, long/short ratio - are public market data or Trader-only analysis; they are under `/market/` today and therefore public, which is the one call in this row that could reasonably go the other way | SRS 3.1.3, SCR-01, SCR-10, SCR-11 | PENDING | T-019, T-024 |
| A-24 | SRS section 5.3 has no message for a refused authorization, and none for a request with no credential other than MSG44 for an ended session. Every other refusal in the system names a message of SRS 5.3 | Add a message for "you are not allowed to do this" (MSG48, since A-15 proposes MSG46 and A-17 proposes MSG47). Until then `ErrorCode.ACCESS_DENIED` borrows the reference-code text of MSG43 exactly as `DATA_CONFLICT` does, and `AUTHENTICATION_REQUIRED` names MSG44, which is the right text for a caller who must sign in again. Both are recorded in the enum | SRS 5.3, 3.1.3 | PENDING | — |
| A-25 | The matrix leaves SCR-02 to SCR-06 blank for Trader and Admin, which would read as "a signed-in caller may not reach the sign-in screens". Taken literally it would forbid `POST /auth/logout` and `POST /auth/refresh` to the very callers who need them | Read the blank as "not applicable to that column" rather than "denied": the six authentication endpoints stay open to everyone, as they have been since T-012. Confirm the reading, or say in 3.1.3 that a blank means only that the screen is not part of that role's navigation | SRS 3.1.3 | PENDING | — |
| A-26 | BR-03 says an account cannot log in for fifteen minutes after five consecutive failures, and BR-04 says a successful reset revokes every refresh token. Neither says what a **password reset** does to the failed-attempt counter, so an account that locked itself out and then reset its password still cannot sign in with the new one until the fifteen minutes are served | Read as: a reset does not clear the lockout. BR-03 says a successful *login* resets the counter and a reset is not a login, and clearing it would make the reset endpoint a way to shorten a lockout without knowing the password. `BR03_aReset_doesNotClearTheFailedAttemptLockout` pins that reading. Confirm it, or state in BR-03 or BR-04 that a reset ends the lockout - the argument the other way is that the holder has just proved control of the address, which is stronger evidence than a password | BR-03, BR-04 | PENDING | — |
| A-27 | SRS 3.2.2 requires a new verification token to invalidate the previous unused ones. SRS 3.2.4 states nothing of the kind for reset links, so by the letter of it every request leaves another working link in the mailbox, each independently valid for thirty minutes | The implementation invalidates the previous unused reset links on every request, borrowing 3.2.2's rule, because the consequence is worse here: presenting a reset link sets a password, while presenting a verification link only confirms an address. Confirm, and say it once in the SRS for both kinds rather than per section | SRS 3.2.4, 3.2.2, BR-04 | PENDING | — |
| A-28 | SRS 3.2.2 caps verification resends at once per 60 seconds and five per day. SRS 3.2.4 puts **no cap at all** on the reset request, so `POST /auth/forgot-password` can be called without limit against one address - a way to flood a mailbox, and the endpoint that must answer identically to everybody and so cannot refuse the caller either | Decide whether the 3.2.2 cap applies to reset links too, or whether this is left to the Bucket4j rate limit of TECHNICAL_DESIGN 5.3, which is per IP and per user and therefore does not protect a single address from many callers. Not implemented in T-013, because a cap the SRS does not state would be a number nobody chose, and because a throttle that refuses is visible in a response that must not vary | SRS 3.2.4, 3.2.2, NSF | PENDING | — |
| A-29 | Two endpoints return the same answer for every address, which SRS 3.2.2 and 3.2.4 require, but not in the same **time**. `requestPasswordReset`: an address that gets a link costs a bulk update, an insert and an event that an unknown or unverified one does not. `resendVerification` is **worse, with three tiers rather than two** - unknown or already verified returns after one query; known, unverified and throttled returns after the throttle check, which is two more queries; known, unverified and not throttled goes on to write and publish. So it leaks not only whether an address holds an unverified account but whether that address has asked recently. `login` in the same class equalises exactly this kind of difference with a bcrypt verification against a hash of nothing, so this is a standard the codebase already sets and neither of these paths meets | Decide the fix when the mail module lands: move the issuing work off the request thread so every case returns after the same lookup, which is the seam A-18 already has to open. **Not a constant delay** - that is a new number nobody chose, it costs every caller, and it leaks under statistics anyway. Found by self-review of T-013; the `resendVerification` half was found when an external review grouped the two endpoints together as solved, which they are at the level of the response body and are not at the level of the clock | SRS 3.2.2, 3.2.4, SCR-05, BR-01, BR-04 | PENDING | the task that adds the mail module |
| A-30 | BR-03 locks an account after five consecutive failed **logins**. SRS 3.2.5 asks for the current password on the Security tab and says nothing about what a wrong one counts towards, so a stolen access token (fifteen minutes) can guess the current password on `PUT /me/password` with no lockout at all | Read as: a wrong current password does not count towards BR-03 — the caller is already signed in, and BR-03's words are about signing in. `BR03_aWrongCurrentPassword_doesNotCountTowardsTheLockout` pins that reading. Confirm, or state that it counts; the other defence is the per-user Bucket4j limit of TECHNICAL_DESIGN 5.3, which is not built yet | BR-03, SRS 3.2.5 | RESOLVED 2026-09-24 — decided by the team lead in the T-014 follow-up: a separate per-account counter (`failed_password_change_count`, V6) with BR-03's threshold of five; the fifth ends every session of the account, the caller's included, and restarts the count; the sign-in is not locked; a successful change resets it. BR-03 itself is unchanged. Recorded in TECHNICAL_DESIGN 7.15 and 13 | — |
| A-12 | `futures_market_data` mixes periodic snapshots (90 days, NSF-17) with funding settlements the P/L must keep for ever (BR-37, A-05). A TimescaleDB retention policy drops whole chunks and cannot filter by column, so no policy on that table can keep one kind and drop the other | Split the settlements into `funding_rate_history (pair_id, funding_time, funding_rate, mark_price)`, primary key `(pair_id, funding_time)`, no retention policy and deliberately not a hypertable; `futures_market_data` keeps periodic snapshots only and drops `snapshot_type`. Done in `V2__timescale_hypertables.sql` beside the policies that force it | NSF-17, BR-37, A-05, logical model | APPROVED 2026-09-20 | — |

---

## 6. Task backlog

`Dep` = dependencies. `Refs` = SRS ids the task implements. `Done when` is the short acceptance criterion; the `NEXT` task also has a detail block in section 7.

### P0 — Foundation (Sprint 0)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-001 | Create repository, folder skeleton and documentation set | DO | — | TD 4 | Structure of TD 4 exists; CLAUDE.md, CURRENT_STATE.md, docs/ committed; `develop` and branch protection configured | **NEXT** |
| T-002 | Backend Maven project, build plugins (compiler, Spotless, JaCoCo) and liveness endpoint | BE1 | T-001, D-02 | TD 1.3, 3, 4 | `./mvnw verify` green with zero compiler warnings; Spotless and JaCoCo bound to the build; `/actuator/health/liveness` returns UP | DONE |
| T-003 | Spring Modulith and ArchUnit architecture tests for layer and module rules | BE1 | T-002 | TD 3.1, 2 | Tests fail when a `calculator` package references Spring or JPA, when a controller reaches a repository, or when a module writes another module's tables | DONE |
| T-004 | Extend `deploy/docker-compose.dev.yml` (DB and Redis already present) with backend, AI service and web; add `deploy/docker-compose.yml` for staging | DO | T-001, Q-08 | TD 12 | `docker compose up` starts all services; health checks green; `deploy/.env.example` lists every key used | TODO |
| T-005 | Physical schema and initial Flyway migration (38 business tables + event publication registry). Flyway 10+ needs the `flyway-database-postgresql` module | BE2 | T-002, A-09, Q-08 | SRS 3.1.5, TD 6 | Migration applies on a clean database; all PK/FK/CHECK/UNIQUE of the logical model present | DONE |
| T-006 | TimescaleDB hypertables, indexes and retention policies | BE2 | T-005 | TD 6 | `ohlcv` and snapshot tables are hypertables; documented indexes created; retention jobs configured | DONE |
| T-007 | Seed data (roles, coins, pairs, strategies, packages, system settings, admin account) | BE2 | T-005, T-006 | SRS 5.1 | Seed is idempotent; a fresh database is usable for manual testing | **PARTIAL** 2026-09-21 |
| T-008 | Common building blocks: `BaseEntity`, `ErrorCode`, `BusinessException`, `GlobalExceptionHandler` (ProblemDetail), `Clock` bean, UUID v7, rounding helpers | BE1 | T-002, T-003 | TD 5.1, 5.2, 5.4 | Error codes map to SRS MSG codes; unit tests cover the mapping; the JaCoCo bundle gate holds with real classes present | DONE |
| T-009 | CI pipeline: build, unit + architecture tests, integration tests, coverage gate, image build | DO | T-002, T-004 | TD 12 | Pipeline green on `develop`; gate blocks a coverage drop | TODO |

**T-007 — seed sets withheld, and what each one waits on.** Each of these lands in its own versioned
migration (`V4__…`) as soon as its question is answered; none of them is guessed in the meantime.

| Withheld seed set | Tables | Waits on | Why it cannot be guessed |
|---|---|---|---|
| The enabled pair list and the coins behind it | `coin`, `crypto_pair` | **Q-05** | The rows carry the tick and step sizes a position size is rounded to (BR-23, BR-30). A placeholder filter becomes a wrong quantity in a plan, and a placeholder list silently answers Q-05. The filters themselves come from the exchange through the NSF-01 job, so only the symbol list and the display order are really seed data |
| The subscription packages | `subscription_package` | **Q-04** | Price, duration, daily AI quota and whether the package allows video (BR-43, BR-50, BR-55). An order copies the package price of the moment (BR-56), so a placeholder price is copied into orders and outlives itself |
| The AI configuration | `ai_configuration` | — (task T-071) | Model, system prompt, temperature and token ceiling are decisions of the AI module, and the model name must not be hard-coded anywhere |
| The news sources | `news_source`, `news_tag` | — (task T-076) | The feed list is administered at run time (UC-49); seeding invented feed URLs would put them in production |

### P1 — Identity (Sprint 1)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-010 | User, profile and token domain model with the account state machine | BE1 | T-008 | BR-01…06 | All legal transitions covered; illegal transitions rejected by tests | **DONE** 2026-09-21 |
| T-011 | Registration and email verification | BE1 | T-010 | UC-01, UC-02, BR-01 | 24h single-use token; resend throttled; MSG01…MSG07 returned | **DONE** 2026-09-21 — UC-01 and UC-02 end to end; BR-01, BR-02, BR-04 proved from endpoint to row |
| T-012 | Login, lockout, JWT access token and refresh rotation | BE1 | T-010 | UC-03, UC-05, BR-03, TD 7.15 | Lockout after 5 failures; refresh reuse revokes the family; tests per BR | **DONE** 2026-09-21 — UC-03 and UC-05 end to end; BR-03 proved clause by clause; reuse revokes the family. Committed as `73d1a96` … `adf2f7a`, merged to `develop` and pushed |
| T-013 | Password reset | BE2 | T-011 | UC-04, BR-04 | 30-minute single-use link; reset revokes all sessions; no account enumeration | **DONE** 2026-09-23 — UC-04 end to end; BR-04 proved clause by clause, including a reset that ends a session opened from another device |
| T-014 | Profile, notification preferences, device registration | BE2 | T-012 | UC-06…08 | Avatar upload validated; FCM token stored and deactivated on logout | **DONE** 2026-09-24 — UC-06 (without the avatar, now T-101), UC-07 and UC-08 end to end. FCM token stored by one atomic upsert and deactivated by key and on logout; access tokens die with their session (D-33); repeated wrong current passwords end all sessions (A-30) |
| T-015 | Authorization: role policies and entitlement handler | BE1 | T-012 | SRS 3.1.3 | Every row of the authorization matrix has an API test | **PARTIAL** 2026-09-21 — every row of SRS 3.1.3 is enforced by the filter chain and proved by an API test driven three ways. The **entitlement handler was not built**: it needs `BillingApi`, which the `billing` module brings in P10, so the dependency column is wrong (Q-12). Committed as `11b4a92` … `e9f31a9`, merged to `develop` and pushed |
| T-016 | Web: register, verify, login, reset, profile screens | FE | T-011…T-014 | SCR-02…07 | Screens work against the API; validation messages match section 5.3 | TODO |
| T-100 | Backend hygiene: adopt Lombok inside the scope TD 1.3 and 3.4 already allow, and move the password pattern out of `service` so the `dto` layer rule holds in bytecode as well as in source | BE1 | T-015 | TD 1.3, 3.3, 3.4; SRS 4.2.5 | `@Getter` and `@RequiredArgsConstructor` used where TD 3.4 permits and nowhere else; `lombok.config` keeps generated members out of the coverage ratio; no `dto` class imports from `service`; the layer rule fails when one does; suite green with no test edited | **DONE** 2026-09-23 — 30 getters and 9 constructors generated; `PasswordPolicy` moved to the `auth` root and the layer rule now fails when a `dto` imports a `service`, which it could not before |

### P2 — Market Data (Sprint 2)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-017 | Binance market data client (REST) with resilience policies | BE2 | T-008 | NSF-01, BR-09 | WireMock tests for success, 429, 418, 5xx; request weight respected | **DONE** 2026-09-24 — Spot and futures public REST client; 429, 418, 5xx, timeouts, malformed bodies and the weight budget tested against a local stand-in server (D-36) instead of WireMock; circuit breaker in the client (D-37) |
| T-018 | Pair and coin model, pair filters (tick, step, min notional) | BE2 | T-005 | BR-07, UC-45 | Rounding helpers tested against real filter values | **NEXT** |
| T-019 | NSF-01 symbol synchronization job | BE2 | T-017, T-018 | NSF-01 | Daily job upserts filters; a pair that stops trading is flagged | TODO |
| T-020 | NSF-02 historical candle backfill | BE2 | T-017 | NSF-02, BR-08 | Gap detection works; re-running inserts no duplicates | TODO |
| T-021 | NSF-03 realtime stream ingestion (kline, ticker, mark price) | BE2 | T-017 | NSF-03, BR-08 | Only closed candles stored; reconnect with back-off; gap triggers backfill | TODO |
| T-022 | Redis price cache and SignalR market hub | BE1 | T-021 | TD 5.6, 9 | Client receives price and candle updates; latency target of SRS 4.2.3 met locally | TODO |
| T-023 | NSF-04 futures metrics (open interest, long/short, funding settlement) | BE2 | T-017 | NSF-04, BR-10, BR-11 | Funding time read from the source, never assumed to be 8h | TODO |
| T-024 | Market data API: pairs, candles, snapshots | BE2 | T-020, T-021 | UC-09 | OpenAPI documented; pagination and timeframe validation tested | TODO |

### P3 — Analysis (Sprints 2–3)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-025 | Incremental indicator engine (SMA, EMA, RSI, MACD, Bollinger, volume SMA) | BE1 | T-020 | BR-12, TD 7.2 | Golden-data tests within 1e-8; incremental equals batch (property test) | TODO |
| T-026 | Swing support/resistance detector | BE1 | T-020 | BR-14, TD 7.3 | Unconfirmed candles ignored; equal lows are not swings | TODO |
| T-027 | Setup score calculator v1.0 with components and version | BE1 | T-025, T-026, A-07 | BR-13, TD 7.4 | Fixture tests for up-trend, down-trend and range; spot has no derivatives component | TODO |
| T-028 | NSF-05 indicator pipeline and persistence | BE1 | T-025…T-027 | NSF-05 | Computed within 10s of candle close; idempotent upsert by PK | TODO |
| T-029 | Analysis API and SignalR push | BE1 | T-028 | UC-10, UC-11 | Insufficient history returns nulls, never a wrong value | TODO |

### P4 — Market UI (Sprint 3)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-030 | Web shell: routing, layout, auth guard, error and message handling | FE | T-016 | SRS 3.1.1 | Route guards match the authorization matrix; MSG display consistent | TODO |
| T-031 | Public home and market list | FE | T-024 | SCR-01, SCR-09 | Realtime prices; Live/Delayed indicator; disclaimer shown | TODO |
| T-032 | Chart component with indicator overlays and panels | FE | T-029 | SCR-10 | Forming candle marked provisional; toggles remembered per device | TODO |
| T-033 | Spot analysis screen | FE | T-032 | SCR-10, UC-10 | Setup score card with component breakdown and disclaimer | TODO |
| T-034 | Futures analysis screen | FE | T-032, T-023 | SCR-11, UC-11 | Funding countdown from `next_funding_time`; OI and long/short charts state the available period | TODO |

### P5 — Trading Plan (Sprints 3–4)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-035 | Position sizing and risk calculator | BE1 | T-018 | BR-23…25, BR-30, TD 7.5 | Worked example of TD 7.6 reproduced; quantity floored to step size | TODO |
| T-036 | Liquidation price calculator with leverage brackets | BE1 | T-035, A-01 | BR-26, BR-27 | LONG and SHORT examples pass; bracket with non-zero maintenance amount covered | TODO |
| T-037 | Warning evaluator (8 warning types, 3 severities) | BE1 | T-036 | BR-28, BR-29 | Every threshold tested at, just above and just below the boundary | TODO |
| T-038 | Trading plan aggregate and state machine | BE1 | T-037 | BR-21, BR-22, BR-32 | Edit allowed only in DRAFT; activation blocked by a BLOCKING warning | TODO |
| T-039 | Trading plan API (create, edit, activate, cancel, list, detail) | BE1 | T-038 | UC-16…20 | Snapshot stored on save and recalculated on activation (BR-31) | TODO |
| T-040 | Web: create/edit plan screen with live risk panel | FE | T-039 | SCR-17 | Panel updates within 300ms; warnings shown with severity | TODO |
| T-041 | Web: plan list and plan detail screens | FE | T-039 | SCR-16, SCR-18 | Status tabs; live position block appears after execution | TODO |

### P6 — Matching engine (Sprints 4–5)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-042 | Matching engine skeleton: partitions, channels, compare-and-set status | BE1 | T-039, T-021 | NSF-07, D-09 | A cancel/fill race produces exactly one outcome | TODO |
| T-043 | Entry fill rules and restart replay | BE1 | T-042, A-04 | BR-33, BR-34 | Replay after downtime equals live processing (test) | TODO |
| T-044 | Exit rules: take profit, stop loss, liquidation, precedence | BE1 | T-043, A-02 | BR-35 | SL applied first when both reached in the same range; liquidation by mark price | TODO |
| T-045 | Fees, funding settlement and realized P/L | BE1 | T-044, A-05 | BR-36…38 | Test vector of TD 7.8 reproduced for LONG, SHORT and liquidation | TODO |
| T-046 | Manual close and NSF-09 plan expiry | BE2 | T-044 | UC-21, BR-39, NSF-09 | Close uses the taker fee; expiry only before a fill | TODO |
| T-047 | Web: close position dialog and position status | FE | T-046 | SCR-19 | Estimated exit price and P/L shown before confirmation | TODO |

### P7 — Journal and performance (Sprint 5)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-048 | Journal record creation from the matching engine (`IJournalWriter`) | BE2 | T-045 | BR-34, BR-40 | Trading never writes the journal table directly (architecture test) | TODO |
| T-049 | Trade review editing | BE2 | T-048 | UC-23, BR-40 | Execution facts immutable for SIMULATED trades | TODO |
| T-050 | Manual trade recording | BE2 | T-048 | UC-24, BR-41 | Validation of times and price order; P/L from user-entered fees | TODO |
| T-051 | Performance statistics queries and views | BE2 | T-049, T-050 | UC-25, BR-42 | Win rate, profit factor, realized R correct on a fixture dataset; ≤ 2s for 5,000 trades | TODO |
| T-052 | Web: journal list, entry detail, manual trade, performance dashboard | FE | T-051 | SCR-20…23 | Source filter separates simulated from manual | TODO |

### P8 — Monitoring and notifications (Sprint 6)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-053 | Watchlist model and API | BE2 | T-018 | UC-12, BR-15, BR-16 | Unique per user and pair; limit enforced from system settings | TODO |
| T-054 | Alert rule model, conditions and validation | BE2 | T-053 | UC-13, BR-17…20 | Price and indicator conditions validated per type | TODO |
| T-055 | NSF-06 alert engine | BE2 | T-054, T-028 | NSF-06, TD 7.9 | Cross semantics, trigger modes and cooldown covered by tests | TODO |
| T-056 | Outbox processor and notification dispatch | DO | T-008 | NSF-15, D-08 | At-least-once delivery, retry ≤ 3, no duplicate in-app rows; adds `spring-modulith-events-jdbc` and re-runs the `event_publication` comparison against the schema that artifact ships (T-005 wrote the table before the artifact was on the classpath) | TODO |
| T-057 | Email adapter (verification, reset, alert, receipt, reminder) | DO | T-056 | NSF-15 | Templates render; failures retried, never lost | TODO |
| T-058 | FCM push adapter and invalid-token handling | DO | T-056, T-014 | NSF-15, F92 | An invalid token deactivates the device row | TODO |
| T-059 | Web: watchlist, alert list, alert dialog, notification center | FE | T-055, T-056 | SCR-12…15 | Unread badge; deep link from a notification to the referenced object | TODO |

### P9 — Community (Sprint 7)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-060 | Post model, coin tags, soft delete | BE2 | T-010 | UC-27, BR-47 | Hidden and deleted posts invisible to other users | TODO |
| T-061 | Cloudinary media adapter (signed upload, delete) | DO | T-060 | BR-44, F93…F95 | Size, type and duration limits enforced server-side | TODO |
| T-062 | Video posting entitlement | BE2 | T-061, T-015 | BR-43 | Without an active subscription the API returns the MSG29 error code | TODO |
| T-063 | Comments, replies, engagement (like, save) | BE2 | T-060 | UC-30…32, BR-45 | One like and one save per user per target (constraint test) | TODO |
| T-064 | Violation reports | BE2 | T-060 | UC-33, BR-46 | One report per user per post; self-reporting rejected | TODO |
| T-065 | Web: community feed, post detail, editor, report dialog | FE | T-063, T-064 | SCR-24…27 | Official posts pinned; media preview | TODO |
| T-101 | Profile avatar upload | BE2 | T-061, T-014 | UC-06, SRS 3.2.5 | The avatar of SCR-07 is uploaded through the Media Storage seam (JPG, PNG or WEBP, at most 2 MB, checked server-side); `PUT /me/profile` accepts only a reference from that store, never an arbitrary URL; replacing or removing an avatar deletes the old file | TODO |

### P10 — Billing (Sprint 8)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-066 | Package and order model, price snapshot, expiry | BE1 | T-010 | BR-54, BR-56 | Order keeps the price at order time | TODO |
| T-067 | VNPay adapter (payment URL, signature, IPN, query) | BE1 | T-066 | NSF-12, BR-53 | Sandbox signature sample verified; response codes handled | TODO |
| T-068 | MoMo adapter | BE1 | T-066 | NSF-12, BR-53 | Same test set as VNPay | TODO |
| T-069 | IPN handler and subscription activation | BE1 | T-067, T-068, A-03 | NSF-12, BR-55 | Duplicate IPN is idempotent; wrong amount and bad signature rejected and audited | TODO |
| T-070 | NSF-13 reconciliation and NSF-14 expiry and reminders | BE1 | T-069 | NSF-13, NSF-14 | Pending orders resolved without an IPN; reminder 3 days before the end | TODO |
| T-071 | Web: packages, checkout, payment result, payment history | FE | T-070 | SCR-30…32 | Result taken from the order status, never from the return parameters | TODO |

### P11 — AI Assistant (Sprint 9)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-072 | AI Service: Fastify app, zod schemas, rate limiting, retry, timeout | DO | T-004 | NSF-16, D-04 | Stateless; no database client in the dependency tree; coverage ≥ 80% | TODO |
| T-073 | Backend AI pipeline: queue, persistence, token accounting | BE1 | T-072, A-06 | NSF-16 | Backend persists the answer; failure marks the message FAILED | TODO |
| T-074 | Context snapshot builder | BE1 | T-028, T-039 | BR-51 | Snapshot contains no personal data (test asserts the payload) | TODO |
| T-075 | Conversations, quota and entitlement | BE1 | T-073, T-015 | BR-50, BR-52 | Quota resets at 00:00 UTC+7; a failed question consumes none; expired subscription is read-only | TODO |
| T-076 | Web: AI assistant screen with context selector | FE | T-075 | SCR-29 | Disclaimer on every answer; upgrade prompt when not subscribed | TODO |

### P12 — News (Sprint 9)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-077 | News source model and crawl log | BE2 | T-005 | UC-49, BR-49 | Interval ≥ 15 minutes enforced | TODO |
| T-078 | NSF-10 crawl, URL normalization, deduplication, coin tagging | BE2 | T-077 | NSF-10, BR-48 | Duplicate URL and duplicate title within 48h skipped; lower-case symbol false positives avoided | TODO |
| T-079 | NSF-11 summarization and sentiment through the AI Service | BE2 | T-078, T-072 | NSF-11 | Only rows without a summary are sent; failures retried next run | TODO |
| T-080 | News API and web feed | FE | T-079 | UC-34, SCR-28 | Filters by coin, sentiment and period; 24h sentiment summary | TODO |

### P13 — Administration (Sprint 10)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-081 | Audit log writer inside the command transaction | BE2 | T-008 | NSF-18, BR-57 | A failed command writes no audit row (test) | TODO |
| T-082 | System settings service with typed access and cache | BE2 | T-081 | UC-51 | Changing a setting takes effect without redeployment | TODO |
| T-083 | User management (lock, unlock, ban, role) | BE2 | T-081, T-015 | UC-42, BR-06, BR-58 | Self-demotion and last-admin demotion rejected | TODO |
| T-084 | Moderation queue and decisions | BE2 | T-064, T-081 | UC-43, BR-61 | All reports of a post resolved together; author and reporters notified | TODO |
| T-085 | Pair and leverage bracket administration | BE2 | T-019, T-081 | UC-45, UC-46, BR-59 | A pair with open positions cannot be disabled | TODO |
| T-086 | Management reports and CSV export | BE2 | T-081 | UC-40, UC-41 | Revenue and activity figures match a fixture dataset | TODO |
| T-087 | Admin console UI (all admin screens) | FE | T-082…T-086 | SCR-33…44 | Every admin screen reachable and permission-checked | TODO |

### P14 — Mobile (Sprint 11)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-088 | Flutter app skeleton, routing, auth, secure token storage | FE | T-012 | SRS 3.1.1 | Token refresh works after app restart | TODO |
| T-089 | Market, watchlist and alert screens | FE | T-088, T-059 | SCR-08…15 | Realtime updates over SignalR | TODO |
| T-090 | Chart and analysis screens (ADR-012 decision required) | FE | T-089, ADR-012 | SCR-10, SCR-11 | Chart library chosen and recorded as an ADR | TODO |
| T-091 | Plan, position and journal screens | FE | T-089 | SCR-18…21 | Position status matches the web | TODO |
| T-092 | Push notification integration and deep links | FE | T-058, T-088 | NSF-15 | Tapping a push opens the referenced object | TODO |

### P15 — Hardening and release (Sprint 12)

| ID | Task | Owner | Dep | Refs | Done when | Status |
|---|---|---|---|---|---|---|
| T-093 | E2E suite for the three main flows | DO | P1…P10 | TD 11.1 | Playwright nightly run green | TODO |
| T-094 | Performance testing against the SRS 4.2.3 targets | DO | T-093 | SRS 4.2.3 | k6 report attached; each target met or a deviation recorded | TODO |
| T-095 | Security pass: OWASP baseline, dependency audit, secret scan | DO | T-093 | SRS 4.2.4 | No High findings open | TODO |
| T-096 | Staging deployment, backup and restore drill | DO | T-094 | SRS 4.2.2 | Restore from backup verified; RTO measured | TODO |
| T-097 | Final SRS and design document update (all A-xx resolved) | BE1 | all | SRS 5.4.1 | No `PENDING` row left in section 5; Record of Changes updated | TODO |
| T-098 | Capstone report package and traceability matrix (BR/UC → code → test) | BE1 | T-097 | — | Every BR maps to at least one test | TODO |
| T-099 | Demo script and rehearsal | Team | T-096 | — | Full demo runs on staging within the time limit | TODO |

---

## 7. Detail block — current NEXT task

### T-018 · Pair and coin model, pair filters (tick, step, min notional)

**Unblocked:** its only dependency, T-005, is DONE. T-019 needs it together with T-017, which is now DONE.

**To do at the start of that session** (written from the task row; the SRS ids have not been read yet): read
BR-07, UC-45, BR-23, BR-30 and TECHNICAL_DESIGN 5.4 and 6, then replace this block with the real one.

**What T-017 leaves ready for it:** `market.client.ExchangeSymbol` already carries `tickSize`, `stepSize`,
`minQuantity` and `minNotional` as `BigDecimal` exactly as the exchange sent them, and `isTrading()`; the model
of T-018 should take its filters from there (through T-019's job), never from a seed — Q-05 is still open and the
seed deliberately holds no pair.

---

## 8. Open questions

| ID | Question | Raised | Blocks | Owner | Status |
|---|---|---|---|---|---|
| Q-01 | Setup score: confirm the weights of BR-13 and the scoring table of each component | 2026-09-18 | T-027 | Team + supervisor | OPEN |
| Q-02 | Confirm the quantitative targets of SRS 4.2 (availability, response times, capacity) | 2026-09-18 | T-094 | Team + supervisor | OPEN |
| Q-03 | Confirm the backend runtime — affects every project file and the deployment image | 2026-09-19 | T-002 | Team | RESOLVED 2026-09-19: Java 21 LTS + Spring Boot 4.1.x + Maven (D-02, ADR-002) |
| Q-04 | Number and pricing of subscription packages for the demo | 2026-09-18 | T-007 (seed withheld), T-066 | Team | **OPEN** — needs, per package: code, display name, price in VND, duration in days, daily AI question quota and whether it allows video posts (BR-43, BR-50, BR-55). Until then `subscription_package` stays empty; a placeholder price would be copied into orders by BR-56 and outlive itself |
| Q-05 | Which 30–50 pairs are enabled at release | 2026-09-18 | T-007 (seed withheld), T-019 | Team | **OPEN** — needs the list of symbols, which of them are spot, futures or both, and the display order. The tick and step sizes are *not* wanted from the team: they come from the exchange through the NSF-01 job. Until then `coin` and `crypto_pair` stay empty, because a guessed filter becomes a wrong position size (BR-23, BR-30) |
| Q-11 | How long a verification mail is throttled before it may be resent | 2026-09-21 | T-011 | Team + BE1 | **ANSWERED BY THE SRS, needs confirming — the question's premise was wrong.** SRS section 3.2.2 states it verbatim: "Resending is limited to once per 60 seconds and 5 times per day per email; a new token invalidates previous unused verification tokens." The row was raised saying the SRS gave no window; it does, and T-011 implements exactly that text rather than a number anyone chose. Two residual points, both recorded rather than guessed: the SRS says *per email* and the implementation counts per account, which coincide while an address identifies one account (A-21 covers neither); and the SRS fixes no boundary for "per day", so the count runs from 00:00 UTC+7 borrowed from BR-50 — **that** is the part still genuinely open, and it is A-21. Close this row once the team confirms the reading |
| Q-12 | T-015 is named "role policies **and entitlement handler**", but the entitlement handler cannot be built where the backlog places it. `@entitlement.has(authentication, 'AI')` calls `BillingApi.hasActiveEntitlement` (TECHNICAL_DESIGN 7.12), and the `billing` module arrives in P10 (T-065, T-066). T-015's dependency column lists only T-012, which is wrong: the task as written cannot be finished before P10 | 2026-09-21 | T-015 (entitlement half), T-062, T-075 | BE1 + Team | **OPEN** — the role half is done and proved; the two matrix rows that need entitlement (SCR-29 AI Assistant, and Post Video on SCR-26) are enforced at their role level (`/api/v1/ai/**` and `/api/v1/media/**` are TRADER) with the subscription check still to come. Decide which: move the entitlement handler into T-066 where `BillingApi` is born, or open a new P10 task for it and cut T-015 down to role policies. Nothing should build the handler against a stub `BillingApi`, because an entitlement source that always answers "no" is indistinguishable from a working one until P10 lands and would pass its own tests |
| Q-13 | T-014's "Done when" says "Avatar upload validated", but SRS 3.2.5 stores the avatar (JPG, PNG or WEBP, at most 2 MB) in **Media Storage**, and the Media Storage adapter is T-061 (Cloudinary, signed upload) in P9. Accepting an avatar URL from the client before that exists would let a profile point at any address on the internet; storing the file anywhere else would be a second media store | 2026-09-24 | T-014 (avatar half) | BE2 + Team | RESOLVED 2026-09-24: the avatar is its own task, **T-101** (depends on T-061 and T-014), and T-014 is DONE without it. `UserProfile.changeAvatar` already exists and nothing calls it yet |
| Q-06 | Flutter chart library (ADR-012) | 2026-09-19 | T-090 | FE | OPEN |
| Q-07 | Hosting for staging (VPS provider and size) and the demo domain. A managed PostgreSQL service usually cannot install TimescaleDB, so self-hosted Docker on a VPS is assumed | 2026-09-19 | T-096 | DO | OPEN |
| Q-08 | Confirm the database stack: PostgreSQL 16 + TimescaleDB 2.x in Docker, EF Core migrations (earlier drafts mentioned Flyway and PostgreSQL 14/15) | 2026-09-19 | T-004, T-005, T-006, T-007, T-009 | BE1 + BE2 | ANSWERED 2026-09-20: PostgreSQL 16 + TimescaleDB 2.x on `timescale/timescaledb:2.30.1-pg16` pinned for dev, Testcontainers and staging; Flyway SQL migrations with the TimescaleDB DDL in its own migration; staging self-hosted Docker on a VPS, no managed PostgreSQL (D-18) |
| Q-09 | Redis image and version for the price cache, pinned the same way as the database image. The dev compose file currently says `redis:7-alpine`; D-18 did not cover it | 2026-09-20 | T-022 | DO | ANSWERED 2026-09-20: `redis:7.4.11-alpine`, the current 7.x patch, pinned in the dev compose file and in TECHNICAL_DESIGN 1.3. Redis is a cache only — losing it must never lose business data. **Pin committed with T-005** (moved from T-004, same file already changed by T-005), so T-004 no longer waits on it |
| Q-10 | Confirm `spring.jpa.hibernate.ddl-auto=validate`, so Hibernate checks the Flyway schema and never writes it. TECHNICAL_DESIGN section 6 already prescribes it and D-18 did not contradict it, but D-18 did not state it either | 2026-09-20 | T-010 | BE1 | ANSWERED 2026-09-20: `validate` in every profile. Flyway is the only thing that writes the schema; Hibernate only checks that the entities match it (TECHNICAL_DESIGN 6, CLAUDE.md section 4) |

Rule: an AI agent never answers an open question by guessing. It implements what is unambiguous, adds or updates the row here and marks the task `PARTIAL` or `BLOCKED`.

---

## 9. Session log

Newest first. One block per working session, format in `CLAUDE.md` section 8.

### 2026-09-24 – T-017 Binance market data client (REST)
- Result: **DONE**
- Summary: new `market` module with `market.client.BinanceRestClient`, an anti-corruption layer over the public
  Spot and USD-M futures REST API: `spotExchangeInfo`, `futuresExchangeInfo`, `klines` (both venues),
  `premiumIndex`, `fundingRates`, `openInterest`, `longShortAccountRatios` — the endpoints T-019, T-020 and
  T-023 need and no others. Wire JSON stays in `BinanceResponseParser`; callers get `ExchangeSymbol`, `Kline`,
  `PremiumIndex`, `FundingRate`, `OpenInterest`, `LongShortRatio`, every decimal parsed from the string with
  `stringValue()` so a JSON number in a price field is refused, not read through a double. Per venue,
  `BinanceRequestGate` pauses at 80% of the weight budget until the next minute, waits out 429 and 418 for their
  `Retry-After` (418 logged at ERROR as an alert, never retried), and opens a circuit breaker after repeated
  failed calls; 5xx and timeouts are retried by Spring's `RetryTemplate`; connect and read timeouts on every call.
  Hosts, budgets, timeouts, retry and breaker settings are `cryptopilot.market.binance.*`.
- Scope held to the task row: **no WebSocket client** — streams, ping/pong, reconnect with jitter, resubscribe and
  gap backfill are T-021 (NSF-03), which depends on this task. The limits T-021 needs were verified and recorded
  in TECHNICAL_DESIGN 7.1.1 for it. No persistence, no Redis, no broadcast.
- Phase 0: every Binance limit re-read from developers.binance.com and the official spot docs repository on
  2026-09-24, with sources, in TECHNICAL_DESIGN 7.1.1 (Spot 6000 and futures 2400 weight per minute, the
  `X-MBX-USED-WEIGHT-1M` header, 429 and 418 with `Retry-After`, bans from 2 minutes to 3 days; streams valid 24 h,
  spot pings every 20 s with a 1-minute pong deadline, futures every 3 minutes with 10 minutes, 5 and 10 incoming
  messages per second, 1024 streams per connection). T-014 carry-over check: `AuthService.refresh` marks the old
  refresh token used and inserts its successor inside one `@Transactional` method — already correct, no change.
- Files: `market/client/*` (client, parser, gate, properties, exception, six domain records, two enums),
  `market/config/BinanceClientConfig`, `application.yml`, `pom.xml` (Surefire excludes the `live` tag)
- Tests: +42 (705 → 747 on this branch); suite 747/747; coverage Domain — / Backend 98.65% line (952/965),
  branches 95.31% (244/256). Two `live` tests excluded from the build, run once by hand against the real exchange
  and passed.
- BR/UC/NSF covered: BR-09 (public endpoints only, tested), BR-08 (`Kline.isClosedAt`), BR-10, BR-11 (next funding
  time read from the source); source access for NSF-01, NSF-02 and NSF-04 (their jobs are T-019, T-020, T-023).
- Decisions: **D-36** (a JDK stand-in server instead of WireMock), **D-37** (resilience from Spring's
  `RetryTemplate` plus an in-client breaker; the client refuses rather than sleeps), both PROPOSED.
- Open questions: none new.
- Next: T-018 (pair and coin model). Also unblocked: T-020, T-023 (by T-017) and T-016 (by T-014).
- Commits, on `feature/T-017-binance-market-data-client` and **unpushed**: `43bb438` feat(market): add binance
  spot and futures rest client · `0d0ee0b` test(market): add a live smoke test excluded from the default build.
  `43bb438` compiles on its own.

### 2026-09-24 – T-014 follow-up: session revocation, A-30, device upsert, avatar split
- Result: **DONE** (T-014)
- Summary: three gaps closed in what T-014 built, and the avatar split out. (1) An access token was still
  accepted for up to fifteen minutes after its session ended; `SessionLivenessValidator` now checks the `sid`
  claim on every request against `countUnusedInSession`, through `LiveSessions` (one-minute in-memory cache,
  evicted per account after the commit of every session-ending path, generation counter against the
  read-before-evict race). (2) A-30: wrong current passwords are counted in `failed_password_change_count` (V6);
  the fifth ends every session of the account without locking the sign-in; success resets it. (3) Device
  registration was read-then-delete-then-insert and failed under concurrency; it is one upsert now. (4) The
  avatar became T-101 and T-014 is DONE.
- Files: `auth/{config/SessionLivenessValidator, config/JwtConfig, service/LiveSessions,
  service/WrongCurrentPasswordRecorder, service/PasswordChangeService, service/FamilyRevoker, service/AuthService,
  repository/UserTokenRepository}`; `user/{UserApi, entity/UserAccount, service/UserService, service/DeviceService,
  repository/UserDeviceRepository}`; `db/migration/V6__password_change_attempt_counter.sql`
- Tests: +24 (768 → 792); suite 792/792; coverage Domain — / Backend 98.42% line (811/824), branches 95.98%
  (215/224). Three existing tests were rewritten because the behaviour they pinned was deliberately changed, and
  each now asserts the stronger guarantee: `LoginAndSessionTest.UC05_theAccessToken_staysValidUntilItExpires`
  became `..._isRefusedOnceItsSessionEnds`; `ProfileControllerTest.UC06_aTokenWhoseAccountIsGone_isNotFound`
  (404) became `..._isRefused` (401, MSG44); `UserTokenRepositoryTest` and `expected-columns.csv` pin exact
  surfaces and grew by `countUnusedInSession` and the V6 column. The race test was run against the previous
  device code and failed there on both races.
- BR/UC/NSF covered: UC-05, UC-07 and UC-08 strengthened; BR-03 unchanged and re-proved; A-30.
- Decisions: D-33 and D-34 extended (see their rows), D-35 unchanged; all three still PROPOSED. A-30 RESOLVED,
  Q-13 RESOLVED, new task T-101.
- Open questions: none new. Note for T-083: BR-06 lock and ban must call `LiveSessions.evictAccountAfterCommit`.
- Found on the way: the codebase had no cache at all, so none was reused; no dependency was added.
- Next: T-017 (Binance market data client); T-016 unblocked.
- Commits, on `feature/T-014-profile-and-devices` and **unpushed**: `8012310` fix(auth): reject access tokens of
  revoked sessions by sid · `289f507` fix(auth): revoke all sessions after repeated wrong current password ·
  `16db72c` fix(user): register device tokens with one atomic upsert. Each compiles on its own and `8012310`
  was also verified with the full suite in its own worktree. Two test updates were folded into `8012310` before
  anything was pushed, so no commit carries a red test.

### 2026-09-24 – T-014 Profile, notification preferences, device registration
- Result: **PARTIAL**
- Summary: UC-06 (all but the avatar), UC-07 and UC-08 end to end. `GET/PUT /me/profile` and
  `PUT /me/notification-preferences` (new `ProfileService`, `ProfileController`); `PUT /me/password` on a new
  `PasswordChangeService` in `auth`, which checks the current password (MSG08 as a 400, D-35), applies BR-02
  and revokes every other session through a new `sid` claim naming the caller's refresh family (D-33);
  `POST /me/devices`, `DELETE /me/devices/{id}` and an optional `fcmToken` on `POST /auth/logout` that
  deactivates that device of the session's account (D-34). `MessageResponse` moved to `common.web` so `user`
  can answer MSG14; `common.config.JacksonConfig` now writes every `BigDecimal` as a plain string (TD 5.4).
- Files: `auth/{controller/PasswordChangeController, service/PasswordChangeService, dto/ChangePasswordRequest,
  dto/LogoutRequest, config/JwtConfig, service/AccessTokenIssuer, service/AuthService, repository/UserTokenRepository}`;
  `user/{UserApi, controller/*, dto/*, service/{ProfileService, DeviceService, UserService},
  repository/UserDeviceRepository, entity/UserProfile}`; `common/{web/MessageResponse, config/JacksonConfig,
  exception/ErrorCode}`
- Tests: +63 (705 → 768); suite 768/768; coverage Domain — / Backend 98.30% line (752/765), branches 95.00%
  (190/200). Two existing tests were edited and neither was weakened: `LoginAndSessionTest` follows the new
  `logout(token, fcmToken)` signature (four call sites, `null` device), and `UserTokenRepositoryTest` pins the
  repository's exact method list, so it grew by `revokeOtherSessions`, with a new test of that query beside it.
- BR/UC/NSF covered: UC-06 (PARTIAL, no avatar), UC-07, UC-08; BR-02 on a third path; BR-30's capital and risk
  ranges on the profile (its leverage and price parts belong to P5); messages MSG01, MSG03, MSG08, MSG14, MSG15,
  MSG41. UC coverage 5 → 8.
- Decisions: **D-33** (`sid` claim), **D-34** (device token ownership and deactivation), **D-35** (a wrong
  current password is 400, not 401), all PROPOSED. TECHNICAL_DESIGN 4.1, 7.15 and 8 updated.
- Open questions: **Q-13 raised** (the avatar needs the Media Storage adapter of T-061); **A-30 raised** (a
  wrong current password does not count towards BR-03, so the endpoint has no lockout until the rate limiter
  exists).
- Found on the way: Docker Desktop was not running, and the first baseline run failed 429 tests on
  Testcontainers alone; the baseline after starting it was 705/705. The first commit of the session landed on
  `develop` by mistake and was moved to the feature branch before anything was pushed; `develop` is back at
  `origin/develop`.
- Next: T-017 (Binance market data client). T-016 (web screens) waits until T-014 is DONE.
- Commits, all on `feature/T-014-profile-and-devices` and **unpushed**: `9972550` refactor(common): share the
  message response between modules · `f0ac7e6` feat(common): write decimals as plain strings in every response
  · `ab3bace` feat(user): show and save the profile and notification preferences · `579f935` feat(user):
  register push devices and deactivate them on sign-out · `7cdc8bf` feat(auth): change the password from the
  security tab. Each was checked out into a separate worktree and compiled on its own.

### 2026-09-23 – T-013 Password reset
- Result: **DONE**
- Summary: UC-04 end to end. `POST /auth/forgot-password` answers MSG12 whatever the address turns
  out to be; a verified account is issued a thirty-minute single-use link, announced as an event and
  stored only as a digest. `POST /auth/reset-password` checks BR-02 first, then spends the link,
  writes the new hash and revokes **every** refresh token of the account in one transaction. The
  three identical token factories became one, `SecureTokenFactory`, rather than a third copy.
- BR-04 is proved clause by clause: the thirty minutes on both sides of the boundary with the fixed
  clock (two tests, not one — a single test would have had to issue its second link from a clock the
  first half had already moved, and would have measured the window from the wrong instant while still
  passing), a second use refused, and the revocation proved against **two** sessions opened from
  different devices plus a third account whose session must survive.
- The revocation test was checked by removing the revocation: `BR04_aSuccessfulReset_endsEverySessionOfTheAccount`
  fails without it. The bulk write is `UserTokenRepository.invalidateUnused` over `REFRESH`, which
  already existed — the detail block predicted a new repository method was needed and it was not,
  because revocation and expiry are the same column.
- Files: `auth/service/{AuthService, SecureTokenFactory}`; `auth/event/PasswordResetTokenIssued`;
  `auth/dto/{ForgotPasswordRequest, ResetPasswordRequest}`; `auth/controller/AuthController`;
  `auth/config/SecurityConfig`; `user/{UserApi, entity/UserAccount, service/UserService}`
- Tests: +30 (675 → 705); suite 705/705; coverage Domain — / Backend 98.03% line (647/660), branches
  95.56% (172/180). New `PasswordResetTest` (21); `AuthControllerTest` 25 → 32; `SecurityConfigTest`
  grew with the endpoint list it pins. Two existing tests were edited and neither was weakened:
  `SecurityConfigTest` pins the public endpoint list deliberately, so it had to grow from six to
  eight, and `AuthServiceTest`/`LoginAndSessionTest` follow the factory rename.
- BR/UC/NSF covered: **BR-04 end to end**, BR-02 on a second path, UC-04; messages MSG03, MSG07,
  MSG12, MSG13. UC coverage 4 → 5.
- Decisions: **D-31** (one factory for every opaque token) and **D-32** (UC-04 lives on `AuthService`,
  not the `PasswordResetService` TD 4.1 listed), both PROPOSED. TD 4.1's auth tree updated to match.
- Open questions / alignment: **A-26 raised** — neither BR-03 nor BR-04 says what a reset does to the
  failed-attempt counter; it is left alone (a reset is not a login) and a test pins that reading, but
  it means an account that locked itself out cannot use its new password until the fifteen minutes are
  served. **A-27 raised** — SRS 3.2.4 does not say a new request invalidates the previous unused links;
  3.2.2's rule was borrowed, because presenting a reset link sets a password. **A-28 raised** — SRS
  3.2.4 puts **no cap at all** on the reset request, so one address can be mailed without limit; not
  implemented, because a cap the SRS does not state would be a number nobody chose and a throttle that
  refuses is visible in a response that must not vary. **A-18 and A-20 widened**: there is now a second
  event carrying a raw link, and the borrowed MSG03 for a confirmation mismatch is on a second screen.
- Next: T-014 (profile, notification preferences, device registration).
- Commits, all on `feature/T-100-lombok-and-layer-cleanup` and unpushed: `de0da82` feat(user): set a
  new password hash on an account · `f6b548c` feat(auth): issue and spend a single-use password reset
  link · `634b356` feat(auth): expose forgot and reset password over http. Each was checked out into a
  separate worktree and compiled on its own, so the branch has no commit that does not build.

### 2026-09-23 – T-100 Backend hygiene: Lombok inside its approved scope, and a layer rule that can fail
- Result: **DONE**
- Summary: Lombok was already a dependency and an annotation processor and was used by nothing; it is
  now used in the two places TD 1.3 and 3.4 already allow and made unable to reach any other.
  `@Getter` replaced 30 hand-written getters on five entities, with their Javadoc moved to the fields
  and the four computing accessors left alone; `@RequiredArgsConstructor(access = PACKAGE)` replaced
  nine pure-assignment constructors. `backend/lombok.config` turns `@Setter`, `@Data`,
  `@EqualsAndHashCode` and `@ToString` into compile errors and keeps generated members out of the
  coverage ratio. Main source went from 4,906 to 4,793 lines (1,842 to 1,757 excluding comments).
- **The defect this uncovered, and why nothing had reported it.** `RegisterRequest` (a `dto`) imported
  `PasswordPolicy` (a `service`) to declare BR-02 as a bean-validation pattern. `LayerRulesTest`
  forbids exactly that and was passing, because `PATTERN` is a constant variable: javac copies its
  value into the annotation and leaves no reference in the bytecode ArchUnit reads. The baseline of
  674/674 is the proof — the rule was green while being broken. `PasswordPolicy` moved to the `auth`
  root package, where a rule both layers read belongs, and `LayerSourceRulesTest` now asserts the same
  table over the import lines. Verified against a probe that reads only a constant: `LayerRulesTest`
  passed it 9/9, the new test refused it by name.
- Also fixed in passing: `PATTERN` hard-coded `{8,64}` beside the `MINIMUM_LENGTH` and `MAXIMUM_LENGTH`
  constants that state the same bound, so the two could have drifted silently. It is built from them
  now; every operand is a constant expression, which is what still lets an annotation declare it.
- Files: `backend/lombok.config`; `common/entity/BaseEntity`; `user/entity/{UserAccount, UserProfile,
  UserDevice}`; `auth/entity/UserToken`; `auth/PasswordPolicy` (moved from `auth/service/`);
  `auth/dto/RegisterRequest`; nine beans across `auth/config`, `auth/controller`, `auth/service`,
  `common/entity`, `user/service`; `architecture/LayerSourceRulesTest` (new)
- Tests: +1 (674 → 675); suite 675/675; **no existing test was edited** — `PasswordPolicyTest` moved
  package with the class it tests and its assertions are untouched. Coverage Domain — / Backend 97.93%
  line (616/629), branches 95.35% (164/172). The line ratio fell 0.19pp because 64 *covered* lines were
  deleted while the 13 uncovered ones stayed exactly as they were; the gate is 70% and the missed count
  did not move.
- BR/UC/NSF covered: none added. BR-02's two statements are now one; SRS 4.2.5 gains a rule that can
  actually fail.
- Decisions: **D-29** (Lombok bounded by configuration, not by memory) and **D-30** (a shared rule
  lives above the layers that read it; the layer table is asserted twice for a reason), both PROPOSED.
- Open questions: none raised, none closed.
- Repo hygiene done first, at the user's request: the accidental truncation in
  `V5__refresh_token_family_invariant.sql` was restored; `deploy/run-backend.ps1` was committed as
  `chore(deploy)`; `feature/T-011-identity-use-cases` was renamed `feature/P1-identity` and pushed —
  32 commits, the first time any of T-006, T-007, T-010, T-011, T-012 or T-015 has left this machine.
  **The branch name still undersells it: T-006 and T-007 are P0 database tasks, so the pull request
  description has to say so.**
- **Found and not fixed, needs its own task:** 94 mentions of local-only documents (`TECHNICAL_DESIGN`,
  `ADR-0xx`) across 62 committed files, which `CLAUDE.md` section 4 forbids. The `pre-commit` hook
  blocks local-only *paths* and attribution text but not these strings. Fixing it touches almost every
  file written so far, so it is not smuggled into this task; new and rewritten comments here cite no
  local-only document.
- Next: T-013 (password reset) — its detail block in section 7 is unchanged and still valid.
- Commits, on `feature/T-100-lombok-and-layer-cleanup`: `87f03b3` build(common): bound lombok to the
  two places it may be used · `4c175a2` refactor(common): read an entity's fields without writing the
  accessor · `6b55aca` refactor(common): inject a bean's collaborators without the assignments ·
  `0d24f3d` fix(auth): put the password rule above the two layers that read it. Unpushed; the branch
  sits on `feature/P1-identity`, which is pushed. `8be18f1` chore(deploy) landed on that branch first.

### 2026-09-21 – T-015 Authorization: role policies and entitlement handler
- Result: **PARTIAL**
- Summary: The role half of SRS 3.1.3 is enforced and proved row by row. A verified access token now
  becomes a caller holding one role — the resource server's default converter reads `scope`/`scp`,
  which these tokens do not carry, so until this task every `hasRole` would have been false and the
  matrix would have refused everybody while nothing looked wrong. The matrix itself is the filter
  chain: the public area, the Trader area, the administration console and the one row both roles
  share (SCR-07's Security tab), still ending in `denyAll`. A refusal now answers with the same
  RFC 9457 body as every other error instead of an empty one.
- **The entitlement handler, the other half of the task's title, was not built and could not be.**
  `@entitlement.has(...)` calls `BillingApi` (TECHNICAL_DESIGN 7.12) and the `billing` module arrives
  in P10 (T-065, T-066); the task row lists only T-012 as a dependency, which is wrong. Raised as
  **Q-12** with the two ways out. Nothing was built against a stubbed `BillingApi`, because an
  entitlement source that always answers "no" is indistinguishable from a working one and would pass
  its own tests. The two matrix rows that need it (SCR-29 AI Assistant, Post Video on SCR-26) are
  enforced at their role level today.
- Files: `auth/config/{SecurityConfig, AccessTokenAuthenticationConverter, SecurityProblemDetailHandler, JwtConfig}`;
  `auth/service/AccessTokenIssuer`; `common/exception/{ProblemDetails, ErrorCode, GlobalExceptionHandler}`;
  `common/web/CorrelationIdFilter`
- Tests: +98 (576 → 674); suite 674/674; coverage Domain — / Backend 98.12% line (680/693), branches
  95.35% (164/172). New classes: `AuthorizationMatrixTest` (80), `AccessTokenAuthenticationConverterTest`
  (11); `ErrorCodeTest` grew to 51 with the two new codes.
- BR/UC/NSF covered: SRS 3.1.3 (every row), SRS 4.2.4 (the role check of the three it requires —
  ownership and entitlement are still to come), BR-05; TECHNICAL_DESIGN 5.1, 5.3, 8.
  `check_traceability.py` now reports **18/61**.
- Decisions: **D-27** (the chain enforces the role matrix, not `@PreAuthorize`) and **D-28** (the
  correlation filter runs ahead of the security chain), both PROPOSED.
- Open questions: **Q-12 raised** (the entitlement handler cannot be dependency-ordered before P10).
  **A-23, A-24, A-25 raised.** Q-04, Q-05, Q-11 untouched, and no row was closed — an agent never
  closes one.
- Found and fixed while finishing this task, neither of it invented work:
  - `CorrelationIdFilter` had no order, so it sat behind Spring Security (order −100) and never ran
    for a request the chain refused. Every 401 and every 403 went out with no id in the logging
    context, no `traceId` in the body and no `X-Correlation-Id` header — the responses somebody asks
    about afterwards were the only ones with nothing to look up. D-28.
  - `/billing/ipn/*` and `/billing/return/{gateway}` would have been swallowed by a `/billing/**`
    rule. They arrive from the gateway's servers or as a browser redirect, carry no bearer token and
    are authenticated by their signature (BR-53), so a Trader rule over them would have broken every
    payment in P10. The three billing paths that are screens are named individually instead, and a
    test fails if anybody tidies them into a wildcard.
- The **SRS 3.1.3 reading**, stated because parts of it are a judgement and not a quotation: Guest is
  not a role and cannot be — a visitor has no account, so it is expressed as the rules that grant
  before authentication is considered. "Trader (Subscribed)" is not a fourth role; SRS 3.1.3 says so
  itself. Admin is refused in the Trader area because the matrix leaves those rows blank and the
  preamble says administrators use only the console. The blanks under SCR-02…06 are read as "not
  applicable" rather than "denied", or a signed-in caller could not log out (A-25). The screen-to-
  endpoint split for market data against analysis is A-23 and is the one call that could reasonably
  go the other way.
- Breakage proof, eight mutations, each restored and the suite re-verified green afterwards. Every
  one was caught:

  | # | Mutation | Tests broken | The test it has to get past |
  |---|---|---|---|
  | 1 | Converter grants any role string | 6 | `AccessTokenAuthenticationConverterTest.BR05_aClaimThatIsNotARole_grantsNoAuthority` |
  | 2 | Converter drops the `ROLE_` prefix | 33 | every admission row of the matrix |
  | 3 | Trader area asks only for a session | 15 | `AuthorizationMatrixTest$TraderArea.SRS313_theTraderArea_refusesAnAdmin` |
  | 4 | Security tab declared after the Trader area | 1 | `AuthorizationMatrixTest$Scr07SecurityTab.SRS313_changingOwnPassword_isAdmittedForBothRoles` |
  | 5 | Billing widened to `/billing/**` | 5 | `AuthorizationMatrixTest.BR53_thePaymentCallbacks_areNotInTheTraderArea` |
  | 6 | Public market data opened for every method | 1 | `AuthorizationMatrixTest$Scr01PublicMarketData.SRS313_theMarketOverview_isOpenedForReadingOnly` |
  | 7 | Refusals carry no body | 2 | `AuthorizationMatrixTest$RefusalsCarryTheStandardBody` |
  | 8 | Correlation filter left behind the security chain | 2 | the same two |

  Three readings worth keeping. **Mutations 4 and 6 are caught by exactly one test each**, and both
  are ordering or method scope rather than a role — the kind of mistake that leaves every role
  assertion passing, so those two tests are the thinnest guards in the task. **Mutation 1 is caught
  only at the unit level**: at the HTTP level a token claiming `SUPERUSER` is refused anyway, because
  no rule grants that authority, so the matrix cannot see the difference — the rule that an unknown
  role grants nothing is real only while `AccessTokenAuthenticationConverterTest` exists.
  **Mutations 7 and 8 break the same two tests**, which is correct rather than redundant: one removes
  the body and the other removes the `traceId` inside it, and only an assertion that reads the body
  can tell either.
- The proof was run three times and the first two results were discarded, both of them silent
  failures that looked like success:
  1. The harness invoked Maven as `cmd /c mvnw.cmd`, which returned an empty shell. Maven never ran,
     no surefire report was written, and all eight mutations were reported as "not caught" — a clean
     bill of health from a run that executed nothing.
  2. The replacement raised `SystemExit` from inside the test runner when no report appeared, which
     aborted the script **after** applying mutation 1 and **before** restoring it. Mutations 2 to 8
     then ran on top of a converter that accepted any role string, which is why the same six
     converter tests failed in every one of them and why mutation 1 itself was skipped on the next
     run as "anchor not unique".
  The harness now restores inside a `finally` and asserts that the restore landed before moving on.
  Worth recording because this is the third distinct way this technique has failed silently in this
  project — T-012's log records the first, where `shutil.copy2` kept an older timestamp and Maven's
  incremental compiler skipped the restored file.
- Branch: `feature/T-011-identity-use-cases`, which now carries T-011, T-012 and T-015. **T-006,
  T-007, T-010, T-011, T-012 and T-015 are all still unpushed**, in that order.
- Next: T-013
- Commits, six, each verified to compile on its own in a detached worktree:
  `11b4a92` refactor(common): build every error body from one factory ·
  `3cd92ec` fix(common): correlate the requests the security chain refuses ·
  `ad22e78` feat(common): name the codes a challenged and a refused request return ·
  `4c9b405` feat(auth): turn the role claim into a granted authority ·
  `d0ca4eb` feat(auth): answer a refused request with the standard problem detail ·
  `e9f31a9` feat(auth): enforce the screen authorization matrix

### 2026-09-21 – T-012 Login, lockout, JWT access token and refresh rotation
- Result: DONE
- Summary: UC-03 and UC-05 work end to end. Every sign-in costs one bcrypt verification — against
  the stored hash when an account holds the address and against a hash of a value nobody knows when
  none does — so the endpoint cannot be used to test addresses; `user` then applies BR-03, BR-06 and
  BR-01 and decides between MSG08, MSG09, MSG10 and MSG11. A session is a 15-minute HS256 access
  token plus a refresh token stored only as a digest, seven days or thirty with "Remember me".
  Rotation retires the token presented and issues a successor in the same family; a retired token
  presented again revokes the whole family before the refusal is raised. A-10's three columns
  arrived first, in two additive migrations.
- Two writes had to survive the refusal that follows them, and both are structural rather than
  careful: BR-03's counter (`FailedLoginRecorder`) and the family revocation (`FamilyRevoker`) each
  commit in `REQUIRES_NEW` from a bean of their own, because a `@Transactional` method called on
  `this` never reaches the proxy and a rollback would otherwise undo exactly the write that makes
  the rule work. A test asserts the counter after a rejected attempt and another presents a retired
  token and then checks that its sibling really stopped.
- Files: `db/migration/V4__login_lockout_and_refresh_family.sql`,
  `db/migration/V5__refresh_token_family_invariant.sql`;
  `auth/config/{JwtConfig,TokenProperties,AccessTokenExpiryValidator,SecurityConfig}`;
  `auth/service/{AuthService,AccessTokenIssuer,RefreshTokenFactory,FamilyRevoker,IssuedSession}`;
  `auth/dto/{LoginRequest,RefreshRequest,SessionResponse}`; `auth/controller/AuthController`;
  `auth/entity/UserToken` (+`issueRefresh`, the family); `auth/repository/UserTokenRepository`
  (+`revokeFamily`); `user/{UserApi,UserSummary,UserRole,LoginCredentials}`;
  `user/service/{UserService,FailedLoginRecorder}`; `user/entity/UserAccount` (BR-03);
  `common/exception/{ErrorCode,BusinessException,GlobalExceptionHandler}`; `application.yml`;
  `pom.xml`; `deploy/.env.example`
- Tests: +122 (456 → 578); suite 578/578; coverage Backend 98.14% line (632/644), branches 95.68% (155/162).
  New classes: `LoginAndSessionTest` (36, the whole of UC-03 and UC-05 against the database),
  `LoginStateMigrationTest` (11), `TokenPropertiesTest` (10), `UserRoleTest` (2);
  `UserAccountTest` grew to 44 with BR-03, `AuthControllerTest` to 25 and `SecurityConfigTest` to 21.
- BR/UC/NSF covered: BR-01 (**now complete** — the domain half was T-010's, the endpoint half is
  here: an unverified account cannot sign in), BR-03 (every clause, including the fifth failure
  exactly, both sides of the 15-minute boundary, and a correct password refused during a lockout),
  BR-06; UC-03, UC-05; SRS 3.2.3; MSG08, MSG09, MSG10, MSG11, MSG44; TECHNICAL_DESIGN 5.3 and 7.15.
  `check_traceability.py` now reports **17/61**.
- Decisions: **D-25** (message arguments on `BusinessException`) and **D-26** ("Remember me"
  survives rotation without a column), both PROPOSED.
- Open questions: none new, and none closed — an agent never closes one. **A-10 RESOLVED** by this
  task's two migrations, with one thing left for a human: the logical model still has to gain the
  three columns, because the schema is now ahead of the document. **A-22 raised**: BR-03 says
  nothing about the counter once a lockout has been served, and the code restarts it at one rather
  than carrying the old count forward — `UserAccount` had promised this row existed and it did not.
  Q-04, Q-05 and Q-11 untouched.
- Found and fixed while finishing this task, none of it invented work:
  - `EntityMappingTest` (T-010's) still built REFRESH tokens through `UserToken.issue`, which the
    new family invariant refuses — two errors, suite red. It now dispatches through the factory each
    kind has, the way `UserTokenTest` and `UserTokenRepositoryTest` already did.
  - `deploy/.env.example` declared `JWT_SIGNING_KEY` while the application reads `JWT_SECRET` and
    has no fallback for it (D-20), so a deployment that followed the example file would have failed
    at start-up. Renamed; `JWT_ISSUER` and `JWT_AUDIENCE` removed, because the issuer is a constant
    in `JwtConfig` and there is no audience claim, so both were keys an operator could set to no
    effect.
- Carried forward, one line each, none resolved here:
  - **A-13** — the logical model's settings keys disagree with BR-17 and BR-44. Owner: Team + BE1.
  - **A-14** — BR-05 describes no way for the first Admin to exist; it is seeded (D-20). Owner: Team.
  - **A-15** — no message for a refused account-status change; MSG39 is borrowed. Owner: Team.
  - **A-16** — no Unban action, so BANNED is terminal by omission. Owner: Team.
  - **A-17** — no generic message for a refused duplicate write. Owner: Team.
  - **A-18** — the event registry would store the raw link in the clear once ADR-010 is switched on.
  - **A-19** — a superseded token is indistinguishable from a redeemed one.
  - **A-20** — no message for a password confirmation mismatch.
  - **A-21** — the SRS fixes no day boundary for the five-a-day resend cap; 00:00 UTC+7 is borrowed.
  - **Q-11** — answered by SRS 3.2.2 verbatim; the team still has to confirm the reading.
- Breakage proof, eight mutations, each restored and the suite re-verified green afterwards. Every
  one was caught, so no mutation is a hole:

  | # | Mutation | Tests broken | The test it has to get past |
  |---|---|---|---|
  | 1 | BR-03 threshold 5 → 6 | 17 | `UserAccountTest.BR03_theThresholdAndTheWindow_areTheValuesTheRuleStates` |
  | 2 | BR-03 lock duration 15 min → 0 | 16 | `UserAccountTest.BR03_theLockoutBoundary_isExclusiveAtItsEndInstant` |
  | 3 | access token TTL 15 min → 24 h | 8 | `TokenPropertiesTest.SRS323_theShippedConfiguration_declaresTheSameThreeWindows` |
  | 4 | rotation retires nothing | 6 | `LoginAndSessionTest.TD715_refreshing_retiresThePresentedTokenAndIssuesASuccessorInTheSameFamily` |
  | 5 | family revocation on reuse removed | 1 | `LoginAndSessionTest.TD715_presentingARetiredToken_revokesTheEntireFamily` |
  | 6 | Remember-me branch collapsed to 7 days | 4 | `TokenPropertiesTest.SRS323_theRefreshWindow_isThirtyDaysOnlyWhenRemembered` |
  | 7 | signature verification skipped | 2 | `SecurityConfigTest.NSF_anAccessTokenSignedWithAnotherKey_isNotACredential` |
  | 8 | failed-count reset on a successful sign-in removed | 2 | `UserAccountTest.BR03_aSuccessfulSignIn_resetsTheCounter` |

  Two readings worth keeping. **Mutation 5 is caught by exactly one test**, and that is the shape to
  expect rather than a gap: the response to a replayed token is MSG44 either way, so nothing about
  the refusal can notice, and only a test that presents a retired token and then checks that its
  *sibling* stopped working can. It is the thinnest guard in the task and the one to keep in mind if
  `LoginAndSessionTest` is ever pruned. **Mutations 3 and 6 are caught by a configuration file being
  read as text**, which is what makes "declared value" more than a phrase: without those two the TTLs
  would only ever be asserted against themselves.
- The first run of this proof was wrong and was discarded. The harness restored each file with
  `shutil.copy2`, which keeps the backup's older timestamp, so Maven's incremental compiler saw a
  source older than its class and skipped it — mutations 3 to 8 ran against the previous mutation's
  compiled code. It showed as mutation 3, a change to one line of `application.yml`, breaking the
  BR-03 lockout tests, which nothing in that mutation can reach. Fixed by touching every restored
  file and deleting `target/classes` before each run; all eight were then re-run from a clean tree
  and the numbers above are the second run's. Worth recording because the failure mode is silent and
  would have been read as unusually thorough tests.
- Branch: `feature/T-011-identity-use-cases`, which now carries T-012 as well. **T-006, T-007,
  T-010, T-011 and T-012 are all still unpushed**, in that order.
- Next: T-013
- Commits, eight, each one verified to compile on its own in a detached worktree — the first
  ordering did not, and was reset and rebuilt: `UserAccount` reaches for `ErrorCode`'s new
  `LOGIN_TEMPORARILY_LOCKED` and the message-argument constructor, so the `common` slice has to come
  before the `user` one, not two commits after it. Nothing about the final tree changed:
  `73d1a96` feat(common): carry the values a message leaves a hole for ·
  `f4814cc` feat(user): lock an account after five failed sign-ins ·
  `338368c` feat(auth): bind every refresh token to a family ·
  `cdaf305` feat(user): publish the role and the credentials a sign-in needs ·
  `6397f70` build(auth): add the oauth2 resource server and the jose encoder ·
  `13ea2c2` feat(auth): issue and verify a signed access token ·
  `992159f` feat(auth): sign in, rotate the refresh token and sign out ·
  `adf2f7a` feat(auth): expose sign-in, refresh and logout over http

### 2026-09-21 – T-011 Registration and email verification (use cases)
- Result: DONE
- Summary: UC-01 and UC-02 work end to end. Registration validates BR-02, encodes with bcrypt at
  cost 12 from a published bean, writes the account and its profile through the `user` module's new
  `UserApi` and issues a 24-hour single-use link, all in one transaction; verification spends the
  token and verifies the address together; the resend follows SRS 3.2.2. The link leaves as a domain
  event published after commit — no mail library, no SMTP client, no outbound call. Spring Security
  arrives with a chain that denies everything not named.
- Files: `auth/config/SecurityConfig`, `auth/service/{AuthService,PasswordPolicy,VerificationTokenFactory}`,
  `auth/controller/AuthController`, `auth/dto/*`, `auth/event/VerificationTokenIssued`,
  `user/{UserApi,UserSummary}`, `user/service/UserService`, `user/repository/UserProfileRepository`,
  `user/repository/UserAccountRepository` (+`flush`), `common/exception/ErrorCode` (+2), `pom.xml`
- Tests: +52 added (27 service, 19 password policy, 13 security config, 12 controller, less the 19
  policy cases that landed with the previous session); suite 456/456; coverage Backend 99.07% line,
  95.69% branch (gate 70%)
- BR/UC/NSF covered: BR-01, BR-02, BR-04, BR-05 (all four now end to end); UC-01, UC-02; SRS 3.2.1,
  3.2.2, 4.2.4; MSG01, MSG02, MSG03, MSG04, MSG05, MSG06, MSG07
- Decisions: D-24 (profile write path — `UserProfileRepository`, a stated exception to D-23)
- Open questions: **Q-11's premise was wrong.** SRS 3.2.2 states the throttle verbatim — "once per
  60 seconds and 5 times per day per email; a new token invalidates previous unused verification
  tokens" — so nothing was invented and nothing was guessed; the row now cites the text and asks the
  team only to confirm the reading. The genuinely open part is the day boundary, which the SRS does
  not fix and which the code takes from BR-50 (00:00 UTC+7): that is A-21. New: A-18 (the event
  registry would store the raw link in the clear once ADR-010's registry is switched on), A-19
  (a superseded token is indistinguishable from a redeemed one), A-20 (no message for a password
  confirmation mismatch), A-21. Q-04 and Q-05 untouched.
- Carried forward, one line each, none resolved here (an agent never closes these):
  - **A-10** — `failed_login_count`, `locked_until`, `token_family_id` do not exist; additive
    migration belongs to T-012. Owner: BE1. PENDING.
  - **A-13** — the logical model's settings keys disagree with BR-17 and BR-44; the seed follows the
    SRS. Owner: Team + BE1. PENDING.
  - **A-14** — BR-05 describes no way for the first Admin to exist; it is seeded (D-20). Owner: Team.
    PENDING.
  - **A-15** — no message for a refused account-status change; `ACCOUNT_STATUS_TRANSITION_INVALID`
    borrows MSG39. Owner: Team. PENDING.
  - **A-16** — no Unban action, so BANNED is terminal by omission rather than by statement. Owner:
    Team. PENDING.
  - **A-17** — no generic message for a refused duplicate write; `DATA_CONFLICT` borrows MSG43's
    reference-code text. T-011 kept this off the registration path by giving the duplicate address
    its own MSG04 on both the checked and the raced path. Owner: Team. PENDING.
  - **Q-11** — answered by SRS 3.2.2 verbatim; needs the team to confirm the reading, and the day
    boundary it does not fix is A-21. Owner: Team + BE1. OPEN pending confirmation.
  - **Q-04, Q-05** — untouched and still OPEN; they gate T-007's withheld seed sets. Owner: Team.
- Deviations from the brief, both reported rather than quiet:
  1. **`UserAccountRepository` gained `flush()`**, which the brief asked not to rewrite the T-011
     repositories without saying so. A criterion forced it. An account assigns its own key, so
     `save` only makes the entity persistent and no statement reaches the database until commit —
     which is *after* `UserService.registerTrader` returns and outside the `try` that turns a
     refused duplicate into MSG04. Without the flush the loser of a concurrent registration got the
     generic conflict of A-17 instead of the message the SRS assigns, which is exactly the failure
     the detail block's "Watch out" warned about. `UserAccountRepositoryTest`'s pinned surface was
     widened by one name to match, and the rule it guards (no unbounded read) is untouched —
     `count` is now asserted absent alongside `findAll`.
  2. **`GlobalExceptionHandlerTest` was scoped** to the controller it declares. Its `@WebMvcTest`
     was unscoped, so the moment a real controller existed the slice tried to build it and failed
     on a service the test has no business knowing about.
- Breakage proof, six mutations, each restored and the suite re-verified green afterwards:
  bcrypt 12→4 (2 failures, incl. the declared-constant assertion); the single-use flag not set on
  redemption (6); the expiry boundary made inclusive (2); registration's single transaction removed
  so the profile insert no longer shares it (11, incl. the rollback test); BR-02's digit clause
  removed (3); `denyAll`→`permitAll` (7). Every mutation was caught, and each annotation- or
  bean-declared value is asserted as a declared value and not only through its effect — which is
  the hole the previous session left.
- D-20, the one-line command that produces `ADMIN_PASSWORD_HASH`, verified working on this machine
  (the hash it prints was confirmed to satisfy the application's own encoder, `matches=true`):
  ```
  cd backend
  ./mvnw -q dependency:build-classpath -Dmdep.outputFile=target/cp.txt -Dmdep.includeScope=runtime
  printf 'import org.springframework.security.crypto.bcrypt.BCrypt;
public class H{public static void main(String[] a){System.out.println(BCrypt.hashpw(a[0],BCrypt.gensalt(12)));}}
' > target/H.java
  java -cp "target/classes;$(cat target/cp.txt)" target/H.java 'the-password'   # ':' not ';' on Linux and macOS
  ```
  Until somebody runs it and supplies the value, the seeded administrator still cannot sign in.
- Branch: `feature/T-011-identity-use-cases`, cut from `feature/T-011-identity-repositories` at
  `fcfa5c5`. **T-006, T-007, T-010 and T-011 are all still unpushed**, in that order.
- Next: T-012
- Commits: `8cc1f0c` feat(common): name the refusals registration needs · `a456204` feat(user):
  create an account and its profile in one transaction · `0f87ce2` feat(auth): issue and redeem
  single-use verification links · `00ab7d4` feat(auth): expose registration and verification over
  http

### 2026-09-21 – T-011 Registration and email verification (persistence half)
- Result: **PARTIAL** — the repositories and the conflict mapping are done; the registration and
  verification use cases are outstanding and keep the T-011 row open.
- **Scope was cut deliberately, and by instruction.** The detail block's acceptance criteria ask for
  UC-01 and UC-02 end to end, which needs services, a controller, Spring Security and the password
  encoder. The session's instructions forbade all four ("no service, controller, DTO, mapper or
  security config unless a criterion names it"; "do not build services, controllers, JWT handling,
  security filters or the login flow"), while its design and test phases described only repository
  work. Those two cannot both be satisfied, so the explicit prohibition was followed, step 1 of the
  block was built in full, and the row stays PARTIAL rather than being quietly redefined as done.
  The remaining steps are unchanged and are written out in section 7.
- Baseline: `./mvnw -B clean verify` green before any edit (341/341).
- Summary: `UserAccountRepository` (user) and `UserTokenRepository` (auth), one per aggregate root,
  plus a handler that turns a refused write into a 409 instead of an unhandled 500.
- **The finding worth keeping (D-23).** The schema enforces case-insensitive uniqueness with a
  functional index on `lower(email)`. Spring Data's derived `IgnoreCase` keyword generates
  `upper(email) = upper(?)` — correct, and unable to use that index, so `existsByEmailIgnoringCase`
  would have been a sequential scan of the account table on every registration. No functional test
  would ever have shown it. Both lookups are therefore explicit JPQL over `lower(...)`, and a test
  reads the plan with `enable_seqscan` penalised and asserts both directions: the `lower` form uses
  `uq_user_account_email_lower`, the `upper` form cannot.
- **Both repositories extend `Repository`, not `JpaRepository` (D-23).** `JpaRepository` would have
  contributed `findAll`, `count` and `deleteAll` to two tables that grow with every registration and
  every sign-in. Listing the operations makes the absence structural instead of a convention, and a
  test asserts that `findAll` does not exist to be reached for. No method returns an unbounded list;
  every read answers with at most one row.
- **Uniqueness is the database's, not the check's.** `existsByEmailIgnoringCase` is an optimisation:
  two registrations can both pass it and the index refuses the second. The test does exactly that —
  passes the check, writes the duplicate, and asserts the violation — and the web boundary now
  answers 409 with a stable code rather than 500 with a stack trace. The constraint name goes to the
  log and never to the response, since it names the tables.
- **No repository predicate touches expiry.** Whether a token may still be used stays
  `UserToken.isUsableAt`, decided against the injected clock. A predicate on `expires_at` would be a
  second copy of BR-01 and BR-04 evaluated against the database's clock, and a link presented one
  second late would look like a link that never existed instead of one that expired.
- Files: `user/repository/UserAccountRepository.java` (new); `auth/repository/UserTokenRepository.java`
  (new); `common/exception/{ErrorCode,GlobalExceptionHandler}.java`; tests
  `user/repository/UserAccountRepositoryTest.java`, `auth/repository/UserTokenRepositoryTest.java`,
  `common/exception/GlobalExceptionHandlerTest.java`.
- Tests: 38 added; suite 379/379; coverage backend 100.00% line (297/297, gate 70%), branches
  96.34%. A repository interface contributes no lines of its own, so the count moved only through
  the conflict handler.
- BR/UC/NSF covered: the persistence half of BR-01 (one account per address, case-insensitively;
  a token found by the digest of the value presented) and of BR-04 (a token is found only as the
  kind it was issued as). No new rule id — BR-01, BR-04, BR-05 were already counted by T-010, and
  none of them is end to end until the use cases exist. `check_traceability.py` still reports
  **15/61**, which is the honest number.
- Decisions: **D-23** (repository shape, read-only reads, explicit `lower(...)` over the derived
  `IgnoreCase`), PROPOSED.
- Open questions: **Q-11 raised** — how long a verification mail is throttled before it may be
  resent (UC-02 says "throttled"; the SRS gives no window), and whether the limit is per account or
  per address. The repository returns the most recently issued token of a kind so a throttle can
  measure against it; no number was chosen. Q-04 and Q-05 stay OPEN and untouched — nothing here
  needed the withheld seeds. **A-17 raised**: SRS 5.3 has no message for a refused duplicate write
  other than the address-specific MSG04, so the generic conflict borrows MSG43's reference-code text.
  Still pending with the team, unchanged: **A-10** (BE1, the BR-03 and refresh-family columns, due
  with T-012), **A-13** (the logical model's example settings keys versus the SRS names),
  **A-14** (BR-05 says nothing about how the first administrator exists), **A-15** (no message for a
  refused administrator status change), **A-16** (a ban is terminal only by omission).
- **Proof the tests bite** (six things broken one at a time, then restored — never committed). The
  existence predicate inverted to `<>`: 11 failures. The token expiry boundary moved from exclusive
  to inclusive: two failures, the entity's own boundary test and the repository test that reads a
  token back and asks it. The conflict handler deleted: the duplicate answered 500 instead of 409.
  The kind filter dropped from the kind-aware token lookup: a reset link verified an address, one
  failure. An unbounded `findAll` added: one failure. And a negative result worth recording —
  dropping `@Transactional(readOnly = true)` from `findById` failed **nothing**, because the
  read-only test opened its own read-only transaction and would have kept passing with every
  annotation deleted. A second assertion now reads the attribute off each method, and re-running
  the same break failed it.
- Notes for the next session: the profile has no write path yet — nothing cascades to it and the
  account repository does not save it, so registration cannot write the two rows together until
  that decision is taken. Three options and their consequences are in the detail block; it is the
  first thing to settle. The encoder still does not exist, so `ADMIN_PASSWORD_HASH` still cannot be
  produced and the seeded administrator still cannot sign in (D-20). **T-006, T-007, T-010 and
  T-011 are all unpushed**, in that order: `feature/T-006-timescale-hypertables` →
  `feature/T-007-seed-data` → `feature/T-010-user-domain-model` →
  `feature/T-011-identity-repositories`, each cut from the one before. They have to reach `develop`
  in that order.
- Next: T-011 (continued) — the registration and verification use cases.
- Commits: eaeb135 feat(common): answer a refused write with a conflict instead of a crash ·
  51ea689 feat(user): add the account repository with case-insensitive lookups · fcfa5c5
  feat(auth): add the token repository with digest-only lookups

### 2026-09-21 – T-010 User, profile and token domain model
- Result: DONE
- **Task id correction.** The session was opened against "T-004". T-004 is the docker compose task
  owned by DO; the user, profile and token domain model is T-010, which was the `NEXT` marker and
  whose detail block was the stated scope. The work was done as T-010 and the commits say so, so
  that no commit attributes backend work to a DO row.
- Scope from the NEXT block: the `user` and `auth` entities mapped onto the schema V1 defines, with
  the account lifecycle as behaviour on the entity rather than setters spread through services.
- Baseline: `./mvnw -B clean verify` green before any edit (251/251).
- Summary: Spring Data JPA arrives with `ddl-auto=validate` (Q-10), `BaseEntity` becomes a mapped
  superclass that also implements `Persistable`, and a Spring-managed entity listener fills the
  audit instants from the injected clock. Four entities — `UserAccount`, `UserProfile`,
  `UserDevice` in `user`, `UserToken` in `auth` — plus five enumerations whose constants are the
  members of the check constraints. No repository, no service, no endpoint: the block's step 4
  offers repositories "only where this task needs them", and nothing here needs one, so they arrive
  in T-011 beside the use cases that query.
- **The mapping decisions (D-21, D-22).** No JPA association exists anywhere in the identity
  tables. Across the module boundary it is forced: `auth` owns `user_token` and may not map
  `user`'s entity, so the token names the account with a plain `UUID` — which is also what a
  reference across an aggregate boundary should look like. Inside `user` it is a choice: an
  association decides a fetch strategy, adds a second way to load a row, and becomes an N+1 the
  moment somebody makes it eager, so the profile is keyed by its account and the device holds an
  id. Two tests guard the absence rather than the presence, because an association added later
  changes no assertion about fields.
- **The aggregate boundary came from the schema, not from intuition.** `user_profile`,
  `user_device` and `user_token` are the only three foreign keys to `user_account` that cascade,
  because they are the account itself; trading history, orders, posts and the audit trail keep the
  default and make the delete fail. So the account is the root, the profile and the device are
  parts of it, and the rows that refuse to be deleted with their author are separate aggregates.
  The cascade in the database expresses the lifetime coupling that the module boundary keeps out of
  the mapping.
- **What the entities deliberately do not enforce.** Only an administrator may grant ADMIN (BR-05)
  is authorization and belongs to T-015. The last active administrator may not be demoted or banned
  (BR-58) needs a count of the other accounts. Locking or banning revokes every session (BR-06):
  the entity records the status change, the service revokes the tokens, because the tokens are
  another module's table. The failed-attempt counter of BR-03 needs columns that do not exist yet
  (A-10, T-012), and no migration was written for them here.
- Files: `backend/pom.xml`; `application.yml`;
  `common/entity/{BaseEntity,AuditInstantListener}.java`; `common/exception/ErrorCode.java`;
  `user/entity/{UserAccount,UserProfile,UserDevice,Role,AccountStatus,TradingStyle,DevicePlatform}.java`;
  `auth/entity/{UserToken,TokenType}.java`; tests
  `user/entity/{UserAccountTest,UserProfileAndDeviceTest}.java`, `auth/entity/UserTokenTest.java`,
  `schema/EntityMappingTest.java`.
- Tests: 90 added; suite 341/341; coverage backend 100.00% line (287/287, gate 70%), branches
  97.44%. The bundle more than doubled and stayed fully covered.
- BR/UC/NSF covered: BR-01, BR-04, BR-05 and BR-06 — the *domain* half of each. The account
  lifecycle, the single-use token and the verification state are proved; the endpoints, the 24-hour
  and 30-minute windows as computed values, and the session revocation are T-011 … T-013.
  `check_traceability.py` now reports **15/61**.
- Decisions: **D-21** (no JPA association in the identity tables) and **D-22** (audit instants from
  one injected clock through one entity listener), both PROPOSED. D-21 is the one worth arguing
  about now, because reversing it later touches every entity written under it.
- Open questions: none new. Q-04 and Q-05 stay OPEN and untouched — nothing in this task depended
  on the withheld seeds. Two alignment items added: **A-15** (SRS 5.3 has no error message for a
  refused administrator status change; MSG39 is named as the nearest one and the code says so) and
  **A-16** (the SRS lists no Unban action, so a ban is treated as terminal — stated only by
  omission today). **A-13 and A-14 from T-007 are both still PENDING**, both waiting on the team:
  A-13 renames the logical model's example settings keys to the SRS ones, A-14 adds a sentence to
  BR-05 about the first administrator being provisioned rather than registered.
- **Proof the tests bite** (six things broken locally one at a time, then restored — never
  committed). A column renamed in an entity (`password_hash` to `password_hashed`): Hibernate
  refused to start, "Schema validation: missing column [password_hashed] in table [user_account]",
  65 tests errored. A `Role.SUPPORT` constant the check list does not permit: exactly one test
  failed, `everyRole_isAValueTheColumnAccepts`, on `ck_user_account_role` — and it failed without
  being edited, because it is driven by `@EnumSource`. `@Enumerated(ORDINAL)` on the role: refused
  at start-up, "wrong column type … found [varchar], but expecting [smallint]", 65 errors. The
  audit listener stopped filling the NOT NULL instants: 28 errors on a null value in column
  created_at. Equality switched to reference identity: two tests failed, the T-008 one and the
  new transient-to-detached one. An eager association added where the design has none: the
  statement-count test failed with 6 statements for 5 rows.
- **One break found a weak test and it was strengthened rather than noted.** The eager association
  was caught by the statement count but not by the no-association assertion, which only looked at
  `UserAccount`; it now iterates all four entities, and re-running the same break failed both
  tests. A second, quieter finding is recorded in the test Javadoc: Hibernate's schema validation
  compares column names and types and **not** nullability — a field declared nullable over a NOT
  NULL column passed validation untouched. That is why the round trips assert the nulls themselves.
- Notes for the next session: the JPA starter now means every `@SpringBootTest` validates the
  mapping, so an entity that disagrees with a migration fails the whole suite, not one test. The
  encoder does not exist yet — T-011 adds Spring Security and `BCryptPasswordEncoder(12)`, and the
  first hash it produces is also what an operator needs for `ADMIN_PASSWORD_HASH` (D-20), so that
  command belongs in the T-011 session block. **T-006, T-007 and T-010 are all still unpushed**:
  `feature/T-006-timescale-hypertables`, then `feature/T-007-seed-data` cut from it, then
  `feature/T-010-user-domain-model` cut from that. They have to reach `develop` in that order.
- Next: T-011.
- Commits: 6529f9c build(common): add spring data jpa and validate the mapping at start-up ·
  be07dd8 feat(common): map the base entity and stamp its instants from the clock · bc36101
  feat(user): add the account, profile and device entities · 7ddac91 feat(auth): add the single-use
  token entity · 6459b02 test(common): assert the identity mapping against the migrated schema

### 2026-09-21 – T-007 Seed data
- Result: **PARTIAL** — everything that approved sources determine is seeded; the two sets Q-04 and
  Q-05 gate are withheld rather than guessed, and are listed in section 6 with what each one needs.
- Scope taken from the NEXT block: decide the seeding mechanism (the task's first decision, which
  had not been made), seed what is unambiguous, leave the rest, and prove the seed is idempotent.
- Baseline: `./mvnw -B clean verify` green before any edit (215/215).
- Summary: `V3__seed_reference_data.sql` seeds sixteen system settings, the three trading strategies
  and one bootstrap administrator with its profile. A repeatable migration in `classpath:db/demo`
  holds a demo trader and is reachable only on the `dev` profile. `SeedDataTest` (34) and
  `DemoDatasetTest` (2) read all of it back out of the database.
- **The decision the task existed to make (D-19).** Reference data is a versioned Flyway migration,
  not a runtime seeder: it is checksummed, applied once, and reviewed beside the schema it depends
  on, and a seeder would have needed application code to run before the application is trusted to
  run. Sample data is a *repeatable* migration in a second location that only `dev` adds, so a
  production database cannot reach it at all — a location is a thing a test can inspect, whereas a
  condition inside a shared file is only as good as the flag that was set. Seeded keys are fixed
  uuid v7 literals (generation happens in the application and would differ per database, leaving no
  row a test or a later migration could name), every instant is the constant `2026-01-01T00:00:00Z`,
  and every insert conflicts on its primary key and does nothing. A collision on any *other* unique
  key is deliberately left to raise: it means a foreign row occupies a business key the seed owns.
- **No credential is committed (D-20).** The administrator's hash is the Flyway placeholder
  `${admin_password_hash}`, supplied already hashed from `ADMIN_PASSWORD_HASH`; with nothing set it
  falls back to `!ADMIN_PASSWORD_HASH_NOT_SET`, which no encoder can match, so the account exists
  and no password opens it. The address is in `.invalid` (RFC 2606), which can never resolve and
  cannot belong to a person, which is also what flags the row as seeded — `user_account` has no
  column for that and V1 is immutable. Note for the operator: **an administrator cannot sign in
  until `ADMIN_PASSWORD_HASH` is set**, and the encoder that produces it is chosen in T-012, so the
  value has to be regenerated if that choice is not BCrypt.
- **What was withheld, and why it is not a placeholder.** `coin` and `crypto_pair` (Q-05): the rows
  carry the tick and step sizes a position size is rounded to, and a guessed filter becomes a wrong
  quantity in a plan (BR-23, BR-30). `subscription_package` (Q-04): an order copies the package
  price of the moment (BR-56), so a placeholder price is copied into orders and outlives itself.
  `ai_configuration`, `news_source`, `news_tag`: configuration owned by modules not yet built, and
  the model name must not be hard-coded anywhere. None of it was smuggled into the demo file either.
- **Which settings were seeded, and the line drawn.** A key is seeded when an approved rule states
  its default or calls the value configurable — BR-15, BR-17, BR-29 (five warning thresholds),
  BR-36 (four fee rates), BR-44 (four media limits), BR-54. The token windows of BR-01 and BR-04 and
  the lockout of BR-03 are *not* seeded: those rules state fixed values and never call them
  configurable, so the task that enforces them decides where they live. Decimal settings are written
  at the scale of the column they will be compared against (rates at eight decimals, user-entered
  percentages at three), so a comparison needs no rescaling.
- Files: `backend/src/main/resources/db/migration/V3__seed_reference_data.sql` (new);
  `backend/src/main/resources/db/demo/R__demo_dataset.sql` (new); `application.yml` (Flyway
  placeholders, production locations); `application-dev.yml` (the demo location);
  `backend/src/test/java/com/cryptopilot/schema/{SeedDataTest,DemoDatasetTest}.java` (new).
- Tests: 36 added; suite 251/251; coverage backend 100.00% line (125/125, gate 70%) — the migration
  adds no production Java, so the bundle is unchanged. No schema change, so the two contract files
  are untouched.
- BR/UC/NSF covered: BR-05 (the bootstrap half — that an ADMIN exists at all; that a self-registered
  account is a TRADER and that only an Admin may grant the role stays with T-011 and T-015), BR-15,
  BR-17, BR-29, BR-36, BR-44, BR-54 (each one the *seeded value* only; that the rule is enforced at
  the boundary belongs to the task that enforces it). `check_traceability.py` now reports **12/61**.
- Decisions: **D-19** (seed mechanism) and **D-20** (no committed credential), both PROPOSED and both
  already load-bearing in committed code — they need confirmation before the first staging deploy.
- Open questions: none new. Q-04 and Q-05 stay OPEN and were restated in section 8 with exactly what
  each one needs decided; neither was answered here. Two alignment items added: **A-13** (the
  logical model's example settings keys do not match BR-17 and BR-44; the SRS names win) and
  **A-14** (BR-05 describes no way for the first Admin to exist; the SRS needs one sentence).
- **Proof the tests bite** (five things broken locally one at a time, confirmed failing, then
  restored — never committed): a fourth strategy row reusing an existing `strategy_code` under a new
  key was refused by `uq_trading_strategy_code`, so the migration never applied and all 36 tests
  errored — which is the intended loud failure, since the conflict target covers the primary key
  only; `role = 'SUPERADMIN'` was refused by `ck_user_account_role`, again all 36; `role = 'TRADER'`,
  which the CHECK permits but the rule does not, failed exactly one test,
  `BR05_theSeededAccount_carriesTheAdminRoleThatOnlyAnAdminCouldOtherwiseGrant`; the profile insert
  moved above the account insert was refused by `fk_user_profile_user`, all 36; the demo trader
  copied into `V3` failed six of `SeedDataTest`, and adding `classpath:db/demo` to the production
  locations failed nine, including `theProductionMigrationLocations_doNotIncludeTheDemoSet`. Worth
  recording: neither demo leak was caught by `DemoDatasetTest`, which passed both times — the demo
  test proves the demo path applies, and the production-path tests are what keep it out. Then
  251/251 green again after restoring.
- Notes for the next session: `ddl-auto=validate` is still not switched on (Q-10 answered it, T-010
  turns it on) — the JPA starter is not on the classpath yet, so nothing validates the mapping
  today. `DemoDatasetTest` creates and drops a second database `cryptopilot_demo` on the shared
  container; a test that needs a database of its own now has a pattern to copy. The T-006 branch
  `feature/T-006-timescale-hypertables` is **still unpushed**, and this branch was cut from it, so
  both have to reach `develop` in order.
- Next: T-010.
- Commits: ed39420 feat(common): seed the reference data a fresh database needs · 1a2545c
  feat(common): keep the development sample data out of production · b5c882f test(common): assert
  the seeded rows and that re-seeding changes nothing

### 2026-09-21 – T-006 TimescaleDB hypertables, compression and retention
- Result: DONE
- Scope taken from the NEXT block: convert the four time-series tables to hypertables with the
  documented chunk intervals, compress the candle tables after sixty days, add the retention
  policies of NSF-17, and decide the question the block flagged — how a policy that drops whole
  chunks can keep funding settlements while dropping periodic snapshots.
- Baseline: `./mvnw -B clean verify` green on `develop` (202/202) before any edit.
- Summary: `V2__timescale_hypertables.sql` splits the settled funding rates out of
  `futures_market_data` into `funding_rate_history`, then converts `ohlcv`, `technical_indicator`,
  `spot_market_data` and `futures_market_data` into hypertables, compresses the two candle tables
  after 60 days segmented by `pair_id, market_type, timeframe`, and adds retention of 7 days on the
  spot snapshots and 90 days on the futures snapshots. `HypertableTest` reads all of it back out of
  `timescaledb_information` rather than trusting the migration.
- **The decision the task existed to make (A-12, APPROVED by the team lead).** `futures_market_data`
  held two kinds of row told apart by `snapshot_type`: periodic snapshots worth 90 days, and
  funding settlements the realized P/L reads and that must outlive them (BR-37, A-05). TimescaleDB
  retention drops whole chunks and cannot look at a column, so the first policy to remove a
  90-day-old chunk would have taken the funding history inside it. A scheduled delete was rejected:
  it would have left those rows in chunks the policy still drops. The settlements therefore moved
  to `funding_rate_history (pair_id, funding_time, funding_rate, mark_price)`, primary key
  `(pair_id, funding_time)`, no retention policy, and deliberately not a hypertable — about three
  rows per pair per day (~55k a year at 50 pairs) needs neither chunking nor compression.
  `snapshot_type` is dropped, so nothing can write a second kind of row into a table that now
  expires. The migration carries the copy-across for any development database that already held
  settlements.
- **Two columns now called `funding_rate` and they are not interchangeable.**
  `futures_market_data.funding_rate` is the predicted rate of the moment, streamed from
  `@markPrice@1s`, which the setup score reads (TD 7.4). `funding_rate_history.funding_rate` is the
  rate that was actually charged, and is the only one the realized P/L may use (TD 7.8). Recorded
  in the migration, in the logical model column comments and in TECHNICAL_DESIGN section 6, because
  substituting one for the other would corrupt every closed trade's P/L silently.
- Files: `backend/src/main/resources/db/migration/V2__timescale_hypertables.sql` (new);
  `backend/src/test/java/com/cryptopilot/schema/{HypertableTest (new),BaselineSchemaTest}.java`;
  `backend/src/test/resources/schema/{expected-columns,expected-enums}.csv`;
  `docs/design/TECHNICAL_DESIGN.md` sections 2, 6, 7.1, 7.8 and 13;
  `docs/design/CryptoPilot_Logical_Model.txt`.
- Tests: 13 added; suite 215/215; coverage backend 100.00% line (125/125, gate 70%) — the migration
  adds no production Java, so the bundle is unchanged. The two contract files moved with the schema:
  443 → 447 columns (`snapshot_type` out, four `funding_rate_history` columns in) and 51 → 50
  enumerations.
- BR/UC/NSF covered: NSF-17 (retention) and the storage half of BR-37 — that the settled funding
  rates cannot be dropped. The rule itself, that realized P/L includes funding, stays with T-045.
  `check_traceability.py` now reports **7/61**.
- Decisions: **A-12 APPROVED 2026-09-20** (see section 5). A-05 reworded to name
  `funding_rate_history` instead of the `FUNDING_SETTLEMENT` rows that no longer exist.
- Open questions: none new.
- **Proof the tests bite** (four rules broken locally one at a time, confirmed failing, then
  restored — never committed): a retention policy added to `funding_rate_history` and the table made
  a hypertable failed `fundingRateHistory_isAPlainTableWithNoRetentionPolicy`,
  `BR37_settledFundingRates_areNotReachableByAnyRetentionPolicy`,
  `onlyTheTwoSnapshotTables_haveARetentionPolicy` and `theFourTimeSeriesTables_areTheOnlyHypertables`;
  a 10-day chunk interval failed `timeSeriesTable_isAHypertableWithTheDocumentedChunkInterval` twice;
  `snapshot_type` left in place failed `futuresMarketData_noLongerCarriesASnapshotType` and the
  column contract. Eight failures in all, then 215/215 green after restoring.
- Notes for the next session: the migration used the `by_range(...)` dimension builder rather than
  the older `create_hypertable(table, column, chunk_time_interval => ...)` signature, which is the
  form TimescaleDB 2.30 expects; `ALTER TABLE ... SET (timescaledb.compress...)` plus
  `add_compression_policy` still work on this version. T-007 must not seed the hypertables.
- Next: T-007.
- Commits: 2404e02 feat(market): convert the time series tables to hypertables · acfdaa3
  test(market): name the funding retention test after the rule it proves

### 2026-09-20 — V1 review fixes and merge of T-002, T-003, T-008, T-005
- Result: DONE
- Summary: An independent review of `V1__baseline_schema.sql` raised four defects and a coverage gap
  while the migration was still unmerged, so V1 was corrected in place rather than patched later.
  The four branches of P0 were then merged into `develop` through two pull requests.
- Findings fixed (decided by the team lead):
  **F1** No foreign key to `user_account` cascades any more except `user_profile`, `user_token` and
  `user_device`. `watchlist`, `alert`, `notification`, `trading_plan`, `trading_journal`,
  `ai_conversation` and `engagement` kept the SQL default instead, so a delete that would erase
  trading history is refused. An account is never hard-deleted (BR-05); it is locked or banned.
  **F2** `version bigint NOT NULL DEFAULT 0` on all 29 tables an entity maps. Without it the first
  `@Version` field would have failed `ddl-auto=validate` at T-010.
  **F3** `created_at` and `updated_at` on those same 29 tables, with no database default, so
  `BaseEntity` writes them from the injected clock.
  **F4** `trading_journal` now rejects a SPOT SHORT and a SPOT position carrying leverage, the two
  guards `trading_plan` already had. A manual journal entry does not come from a plan, so the rule
  has to sit on both tables.
  **F5** `trading_strategy.strategy_code` deliberately keeps no CHECK: it is a seeded lookup table
  whose rows are the list. Recorded in the T-005 deviations.
- Remaining cascades, all from an aggregate root to rows that are part of it (18, pinned by
  `SchemaCatalogueTest.onlyAggregateRoots_cascadeTheirDeletes`): `user_profile`, `user_token`,
  `user_device` → `user_account`; `leverage_bracket` → `crypto_pair`; `alert` → `watchlist`;
  `trading_plan_warning` → `trading_plan`; `ai_message` → `ai_conversation`; `post_coin`,
  `forum_comment`, `engagement`, `post_media`, `post_report` → `forum_post`; `forum_comment`,
  `engagement` → `forum_comment`; `news_crawl_log` → `news_source`; `news_article_tag`,
  `news_article_coin` → `news_article`; `news_article_tag` → `news_tag`. Plus one SET NULL:
  `notification.alert_id`, so a deleted alert does not take the notification history with it.
- New tests (16 added, suite 186 → 202): a column contract of all 443 columns with type, precision
  and nullability (`expected-columns.csv`), which is what catches a dropped attribute or an
  unapproved one such as `setup_bias`; every one of the 51 enumerations offered a value outside its
  list on a temporary clone of its table, with the value lists themselves pinned
  (`expected-enums.csv`); the numeric precision rule derived from the column name instead of a
  hand-written list; the cascade set and the no-cascade-to-`user_account` rule; no database default
  on a uuid primary key; `event_publication` compared by type and nullability; BR-05 (an account
  with a journal or plans cannot be deleted) and BR-21 (no spot short in the journal).
  Each new rule was broken locally one at a time and confirmed to fail the intended test; ten
  proofs in all, none committed.
- Files: `backend/src/main/resources/db/migration/V1__baseline_schema.sql`;
  `backend/src/test/java/com/cryptopilot/schema/{SchemaColumnContractTest,SchemaCatalogueTest,EnumCheckConstraintTest,SchemaConstraintTest}.java`;
  `backend/src/test/resources/schema/{expected-columns,expected-enums}.csv`;
  `deploy/docker-compose.dev.yml`; `docs/design/TECHNICAL_DESIGN.md` sections 5.4, 5.5 and 6.
- Tests: 16 added; suite 202/202; coverage backend 100.00% line (125/125, gate 70%) — the changes
  add no production Java, so the bundle is unchanged.
- BR/UC/NSF covered: BR-05 and BR-21 added to the database half already proved for BR-15, BR-45,
  BR-46 and BR-49. `check_traceability.py` now reports **6/61**.
- Decisions: none new. **A-11 APPROVED** — `version`, `created_at` and `updated_at` are physical
  columns of the design, not business attributes, so the ERD stays unchanged. It is numbered A-11
  and not A-10 because A-10 was already taken by the BR-03 lockout and refresh-token-family item
  that T-005 raised and that is still PENDING.
- Open questions: none new. Q-09 now notes that the Redis pin was committed with T-005 rather than
  T-004, because T-005 had already changed that file.
- Merges: PR #1 `T-002: backend Maven project, build plugins and architecture tests` → `223806f`;
  PR #2 `T-008 and T-005: common building blocks and the baseline database schema` → `14fe422`.
  Both merged with `--merge` (no squash, no rebase); both branches deleted. `main` untouched.
  `./mvnw -B clean verify` green on `develop` after each merge, 12/12 then 202/202.
- Next: T-006.
- Commits: d73e3e3 chore(deploy): pin redis image to 7.4.11-alpine · ee29513 fix(common): stop
  cascading deletes of trading history · e137f36 fix(common): add version and audit timestamps to
  mutable tables · e139f56 fix(trading): reject spot short positions in the journal · 4a2949d
  test(common): assert the full column contract of the baseline schema · 2580a1a test(common):
  cover every enum check, cascade rule and numeric kind

### 2026-09-20 — Q-09 and Q-10 decided (no task id)
- Result: DONE
- Summary: Closed the two questions T-005 raised rather than guessed. Neither needed code: Q-09 is an image tag, Q-10 confirms a setting that TECHNICAL_DESIGN 6 already prescribed. No commit was made.
- Decisions: **Q-09 ANSWERED** — the price cache runs `redis:7.4.11-alpine`, the current 7.x patch (published 2026-09-18), taken from the registry rather than assumed and pinned the same way as the database image. Redis stays a cache: losing it must never lose business data. **Q-10 ANSWERED** — `spring.jpa.hibernate.ddl-auto=validate` in every profile, so Flyway is the only writer of the schema and Hibernate only checks that the entities match it.
- Files: `CURRENT_STATE.md` sections 8 and 9, `docs/design/TECHNICAL_DESIGN.md` section 1.3, and `deploy/docker-compose.dev.yml` (image tag `redis:7-alpine` → `redis:7.4.11-alpine`). The compose file is a repository file and was deliberately **left unstaged and uncommitted** — T-004 commits it with its own change.
- Tests: none — decisions only. The suite is unchanged at 186/186.
- BR/UC/NSF covered: none.
- Open questions: none new. Q-09 and Q-10 were the last two raised by T-005; nothing in P0 is now waiting on a decision.
- Next: unchanged, T-006. The `validate` setting has nothing to configure yet, because JPA arrives with the first entity in T-010; T-010 writes it into the profiles.
- Commits: none.

### 2026-09-20 – T-005 Physical schema and the first Flyway migration
- Result: DONE
- Scope taken from the NEXT block: the 38 business tables of the logical model plus the event publication registry, with every PK, FK, CHECK and UNIQUE the model states and the numeric precision of TECHNICAL_DESIGN 5.4. Acceptance: the migration applies from empty on a clean container of the pinned image; an integration test with Testcontainers proves it rather than a manual check; re-running is a no-op; verify green with the gates holding. Dependencies T-002 DONE, A-09 APPROVED, Q-08 ANSWERED — none blocking.
- Baseline: `./mvnw -B clean verify` green (121/121) before any edit.
- Summary: `V1__baseline_schema.sql` creates 39 tables — 38 business plus `event_publication` — with a primary key on every one, a foreign key index on every referencing column, the unique constraints and value checks of the model, and `timestamptz` throughout. Two integration tests run against a real `timescale/timescaledb:2.30.1-pg16` container: `BaselineSchemaTest` asserts the shape over the system catalogue, `SchemaConstraintTest` tries to break each rule and asserts the database refuses the row.
- Files: `backend/pom.xml`; `backend/src/main/resources/application{,-dev,-prod}.yml`; `backend/src/main/resources/db/migration/V1__baseline_schema.sql`; `backend/src/test/java/com/cryptopilot/support/TestcontainersConfig.java`; `backend/src/test/java/com/cryptopilot/schema/{BaselineSchemaTest,SchemaConstraintTest}.java`; `backend/src/test/java/com/cryptopilot/LivenessEndpointTest.java`; `deploy/docker-compose.dev.yml`
- Tests: 65 added; suite 186/186; coverage backend 100.00% line (125/125, gate 70%) — the migration adds no Java, so the bundle is unchanged
- BR/UC/NSF covered: SRS 3.1.5 (physical data model). Four rules are enforced by the schema itself and now carry their id in the test name, so `check_traceability.py` reports **4/61** instead of 0/61: BR-15, BR-45, BR-46, BR-49. Only the database half of each is proved here; the limits, messages and service behaviour stay with T-053, T-063, T-064 and T-077.
- Decisions: none new. D-18 is now exercised end to end — the same image tag runs the dev container, the test container and staging.
- Open questions: none new. **A-10 raised** (see section 5): the logical model has no columns for the BR-03 lockout state or the refresh-token family of TECHNICAL_DESIGN 7.15. Both are additive migrations inside T-012, so nothing is blocked now.
- Next: T-006.
- Commits: b394e48 build(common): add the postgresql and flyway runtime · 9708a13 feat(common): add the baseline schema migration · e61876d test(common): name the schema tests that prove a business rule

**Two real defects the tests caught before they could reach anyone**
- **`flyway-core` alone never runs a migration on Spring Boot 4.** Boot 4 moved the Flyway auto-configuration into its own module, so the plain library sits on the classpath and does nothing at all. The first test run failed on a missing `Flyway` bean, which is what exposed it; the fix is `spring-boot-starter-flyway`. Worth knowing generally: on Boot 4 a bare third-party library is no longer enough, the starter is.
- **The PostgreSQL driver cannot bind a `java.time.Instant`.** Raw JDBC needs `OffsetDateTime`. This does not affect entities — Hibernate converts `Instant` itself — but it will affect every native query and every test that writes rows directly, so T-006 and T-007 should expect it.

**Deviations**
- **No `spring-boot-starter-data-jpa` yet.** Flyway needs a data source, not an ORM, so only `spring-boot-starter-jdbc` was added. JPA arrives with the first entity in T-010, which is also when Q-10 (`ddl-auto=validate`) has to be answered. This keeps T-005 clear of that question.
- **No second descending index on `ohlcv`.** TECHNICAL_DESIGN 6 lists the primary key as `(pair_id, market_type, timeframe, open_time DESC)`. A PostgreSQL primary key cannot declare a direction, and it does not need to: with the three leading columns bound by equality the planner reads the index backwards at the same cost. A duplicate descending index would only slow down the table that takes the most writes.
- **Three indexes beyond the list in section 6**: `trading_journal(pair_id)`, `engagement(post_id)` and `engagement(comment_id)`. Each is the child side of a foreign key whose only other index is partial, and a partial index does not cover a parent delete. `BaselineSchemaTest.everyForeignKeyColumn_isTheLeadingColumnOfSomeIndex` now enforces that rule for every future table.
- **A unique index on `lower(email)`** in addition to the unique constraint the model shows. The SRS compares addresses case-insensitively, so without it two accounts could differ only in case.
- **Five checks the logical model implies but does not spell out**: a comment cannot be its own parent; a subscription ends after it starts; a resolved report names its resolver; a limit plan carries the entry price it waits at; a pair cannot quote itself. Each is listed here so a reviewer can object to any of them individually.
- **`trading_strategy.strategy_code` carries no CHECK.** The logical model annotates it `"BREAKOUT, SWING, SCALPING"`, the same way it annotates a real enumeration, but the table is a seeded lookup with a name and a description per row: the rows are the list, and a CHECK would have to be migrated every time the team adds a strategy. Decided by the team lead on 2026-09-20; recorded here so the reviewer sees it was a choice and not an omission.
- **`currency` is checked against `'VND'`** on package and order. The model documents it the way it documents an enumeration, and every amount column uses the VND scale. Adding a second currency will need a migration, which is what a check constraint is for.
- **`event_publication` uses the v2 structure** Spring Modulith 2.1 expects, with `status`, `completion_attempts` and `last_resubmission_date`. Its own schema initializer stays off, so this migration remains the single source of the schema. The archive table is not created: it is only needed in archive completion mode, which T-056 decides.

**Proof the tests bite** (a bad table added locally, confirmed failing, then deleted — never committed)
- A table with no primary key and a naive `timestamp` column failed three assertions at once: `everyTable_hasAPrimaryKey`, `everyInstantColumn_isTimestampWithTimeZone` and `schema_holdsTheTechnicalTablesAndNothingElse`. After deleting it: 186/186 green, all coverage checks met, BUILD SUCCESS.

**End-to-end check on the real dev database** (container started, then removed with its volume)
- `docker compose -f deploy/docker-compose.dev.yml up -d db` on the pinned tag gives PostgreSQL 16.15 with the `timescaledb` extension already present.
- The application on the `dev` profile logged `Migrating schema "public" to version "1 - baseline schema"`, then `Successfully applied 1 migration`, then `Started CryptoPilotApplication`; `/actuator/health` answered UP and `public` held 40 base tables.
- Host note for the team: something already listens on port 5432 on this machine, so the compose database was published on `DB_PORT=55432` and the application pointed at it with `DB_URL`. Both overrides work; T-004 should keep `DB_PORT` configurable for exactly this reason.

**Follow-ups for later sessions**
- `deploy/.env.example` does not yet list `DB_URL`, which the application reads on the `dev` and `prod` profiles. T-004 owns that file.
- Every `@SpringBootTest` now needs Docker. T-009 has to make the CI runner provide it, or split the suite so the unit and slice tests can still run without it.
- A-07 (`setup_bias` on `technical_indicator`) is still PENDING. Once approved it is an additive migration in T-026, never an edit to V1.
- `LayerRulesTest` still passes `allowEmptyShould(true)` everywhere. Nothing changed here, because T-005 added no Java to the module layers.

### 2026-09-20 — Q-08 and A-09 decided (no task id)
- Result: DONE
- Summary: Recorded the database decisions that were holding P0. Q-08 is answered and A-09 approved; both are now
  binding as D-18. No code was written and nothing was committed.
- Decisions: **D-18 APPROVED** — PostgreSQL 16 with TimescaleDB 2.x on `timescale/timescaledb:2.30.1-pg16`, the same tag pinned in the
  dev compose file, in Testcontainers and on staging; the schema is owned by Flyway SQL migrations with the
  TimescaleDB DDL in a migration of its own; staging is self-hosted Docker on a VPS, never a managed PostgreSQL
  (a managed service cannot install the extension). **A-09 APPROVED** — `event_publication` (Spring Modulith
  registry) and `flyway_schema_history` are technical tables, not business entities, and stay outside the ERD.
- Image tag: `2.30.1-pg16` is the current stable 2.x build for PostgreSQL 16 (published 2026-09-17), taken from the
  registry rather than assumed. The plain tag was chosen over `-oss` on purpose: compression and continuous
  aggregates are Timescale-licensed features, and TECHNICAL_DESIGN section 6 relies on compression.
- Files: `CURRENT_STATE.md` sections 3–9, `docs/design/TECHNICAL_DESIGN.md` section 6, and
  `deploy/docker-compose.dev.yml` (image tag `latest-pg16` → `2.30.1-pg16`). The compose file is a repository file
  and was deliberately **left unstaged and uncommitted** — T-004 or T-005 commits it with its own change.
- Tests: none — decisions only. The suite is unchanged at 121/121.
- BR/UC/NSF covered: none.
- Open questions: two items of the Q-08 detail block were not covered by the answer and were raised rather than
  guessed. **Q-09** — the Redis image and version, which belongs in the same compose file. **Q-10** — whether
  `spring.jpa.hibernate.ddl-auto=validate` stands; TECHNICAL_DESIGN section 6 already prescribes it, so this is a
  confirmation, not an open design choice, and it does not block T-005.
- Next: T-005. T-004 is also unblocked for DO and can run in parallel, once Q-09 gives it a Redis tag.
- Commits: none.

### 2026-09-20 – T-008 Common building blocks (shared kernel)
- Result: DONE
- Scope taken from the NEXT block: the `common` module gives every later module one error model, one base entity, one clock and one rounding policy. Acceptance: every `ErrorCode` maps to exactly one SRS `MSGxx` id, proved by a test over the enum; `GlobalExceptionHandler` answers a business exception, a not-found and a validation failure with a `ProblemDetail` (slice test, no `@SpringBootTest`); `Rounding` has boundary tests for each `RoundingMode` it exposes; two consecutive `UuidV7` values sort in generation order; `./mvnw clean verify` green with the JaCoCo gates no longer vacuous. Dependencies T-002 and T-003 both DONE; no open question blocks the task.
- Baseline: `./mvnw -B clean verify` green (12/12) before any edit, on `feature/T-002-backend-project`.
- Summary: Added the ten classes of the shared kernel with their tests. `ErrorCode` ties a stable code to an HTTP status and an SRS message id; `BusinessException` and `ResourceNotFoundException` carry it; `GlobalExceptionHandler` extends Spring's `ResponseEntityExceptionHandler` and answers RFC 9457 `ProblemDetail` with `code`, `messageCode`, `traceId` and, for validation, a field-by-field `errors` map. `UuidV7` wraps `Generators.timeBasedEpochGenerator()`; `Rounding` holds the whole numeric policy of TD 5.4 with an explicit `RoundingMode` on every operation; `ClockConfig` publishes the single UTC clock; `BaseEntity` carries identity plus audit fields; `CorrelationIdFilter` puts a request id in the MDC and echoes it; `PageResponse` is the paged response shape. `common` is declared an open Spring Modulith module, as TD section 2 requires.
- Files: `backend/pom.xml`; `backend/src/main/java/com/cryptopilot/common/` (`package-info.java`, `config/ClockConfig`, `entity/BaseEntity`, `exception/{ErrorCode,BusinessException,ResourceNotFoundException,GlobalExceptionHandler}`, `util/{UuidV7,Rounding}`, `web/{CorrelationIdFilter,PageResponse}`); `backend/src/test/java/com/cryptopilot/common/` (one test class per production class)
- Tests: 109 added; suite 121/121; coverage backend 100.00% line (125/125, gate 70%), branch 97.62% (41/42); no `calculator` package exists yet, so the 90% rule matches nothing
- BR/UC/NSF covered: none directly — this is infrastructure. `MSG01`, `MSG41` and `MSG43` now have code and tests behind them. `check_traceability.py` is unchanged at 0/61: it reads rule ids out of test method names (`BR28_...`) and no BR formula was implemented here.
- Decisions: none new. D-06 (`BigDecimal` only) and D-07 (application-generated UUID v7) are now load-bearing in committed code while still marked `PROPOSED` — worth confirming at the next stand-up, together with D-05, since nothing in the code contradicts them.
- Open questions: none new. Q-08 now blocks every remaining P0 task except T-001.
- Next: Q-08 (decision). T-005 becomes the next coding task the moment it is answered.
- Commits: e5ca10b build(common): add the uuid v7 generator dependency · f876a1a feat(common): add uuid v7 identifiers and the rounding policy · 42ab39c feat(common): add the utc clock bean · dc142dc feat(common): add the base entity with uuid v7 identity · 03ebdb8 feat(common): put a correlation id on every request · 0eb62cf feat(common): map errors to rfc 9457 problem details · 301453d feat(common): add the paged response shape

**Branch situation (needs a human decision)**
- The T-003 commits were made on `feature/T-002-backend-project` rather than on a branch of their own, so that branch now holds both T-002 and T-003.
- `feature/T-008-common-building-blocks` was created from that branch's HEAD (c2a5bbb), so it contains T-002, T-003 and T-008. Nothing has been pushed; `develop` still has none of it.
- Consequence: the first pull request will carry three tasks unless T-002 and T-003 are merged to `develop` first. Recommended order: push and merge `feature/T-002-backend-project` into `develop`, then rebase the T-008 branch onto `develop` so its pull request shows only the shared kernel.

**Deviations**
- **`BaseEntity` carries no JPA annotations.** The block allowed either. Mapping it now would pull `spring-boot-starter-data-jpa` forward from T-005, and that starter needs a datasource for the application context, which would break `LivenessEndpointTest` and force the Q-08 answer inside this task. The class therefore keeps plain fields plus `markCreated(Instant)` and `markUpdated(Instant)`, which T-005 wires to the JPA lifecycle callbacks. No JPA dependency was added.
- **`BusinessException` takes a detail string, not an argument array.** TD 5.1 sketches `new BusinessException(ErrorCode.X, args)`. The placeholders of SRS 5.3 (`{field}`, `{max}`, `{minutes}`) belong to the message text, which the client owns; the backend sends `messageCode` and lets the client interpolate. None of the three codes in this task has a placeholder the server could fill, so an argument array would have been an unused parameter. Revisit if a later use case needs server-side values in a message.
- **Only three `ErrorCode` constants.** 403 and 401 have no SRS message that fits and cannot be exercised without Spring Security, which arrives with T-012 and T-015. Adding constants no handler can raise would have made the enum test vacuous.
- **Spring's own web exceptions keep their plain body.** An unknown path, a wrong method or an unsupported media type is answered by `ResponseEntityExceptionHandler` with a bare RFC 9457 body — correct status and `detail`, but no `code` or `messageCode`. Verified on the running server: `GET /api/v1/does-not-exist` returns `404 application/problem+json` without those properties. Decide when the first real endpoints land (T-011) whether to enrich every problem detail; doing so needs either new `ErrorCode` constants or a new SRS message id, so it is an SRS-alignment question rather than a code change.
- `java-uuid-generator` 5.2.0 was added with its version in `<properties>`, as ADR-002 prescribes for libraries outside the Spring Boot BOM. ADR-009 already names the library, so no new ADR was needed.

**Proof the gates bite** (violations created locally, confirmed failing, then deleted — never committed)
- `com.cryptopilot.trading.calculator.TempUntestedCalculator`, 60 statements and no test → `Rule violated for bundle cryptopilot-backend: lines covered ratio is 0.66, but expected minimum is 0.70` and `Rule violated for package com.cryptopilot.trading.calculator: lines covered ratio is 0.00, but expected minimum is 0.90`. Both JaCoCo rules now fail the build; before T-008 the bundle held zero classes and passed vacuously.
- The same class annotated `@Component` → `LayerRulesTest.calculators_arePureJava` failed. The architecture rules still bite with real classes on the classpath.
- After deleting the class: 121/121 green, `All coverage checks have been met`, `BUILD SUCCESS`.

**Smoke check on a running server** (dev profile, then stopped)
- `GET /actuator/health/liveness` → `200`, `X-Correlation-Id: 01a0bc46-dbab-7585-...` generated by the filter.
- The same request with `X-Correlation-Id: smoke-t008` → the caller id is echoed unchanged.
- `GET /api/v1/does-not-exist` → `404 application/problem+json`, correlation id present (see the deviation above).

**Follow-ups for later sessions**
- `common.config` still lacks `JacksonConfig` (serialize `BigDecimal` as JSON strings, TD 5.4), `CorsConfig`, `OpenApiConfig` and `AsyncConfig`, and `common.web` lacks `RateLimitFilter`. None is in the T-008 acceptance criteria and none can be tested without endpoints, so each belongs to the task that first needs it — `JacksonConfig` to the first API task (T-011), `RateLimitFilter` to T-012, `CorsConfig` and `OpenApiConfig` to T-009 or T-011.
- `LayerRulesTest` still passes `allowEmptyShould(true)` on every rule. `entity` and `config` now have classes, so those two rules can drop the flag; the rest wait for T-005 and T-011.
- `FixedClock` and the other test builders of TD 11.3 are not written yet. `BaseEntityTest` uses `Clock.fixed(...)` directly; move it into `src/test/java/com/cryptopilot/support` when a second test needs it.
- `BaseEntityTest` reaches the private `id` field by reflection to build two objects that stand for the same row. When T-005 maps the class, replace that with a real load through the repository.

### 2026-09-19 – T-003 Spring Modulith and ArchUnit architecture tests
- Result: DONE
- Scope taken from the NEXT block: enforce the layer rules of TD 3.1 and the module boundaries of TD 2 as tests that fail the build, before any module code exists to violate them. Acceptance: `./mvnw verify` runs both test classes and stays green; a `calculator` class importing Spring or JPA fails `LayerRulesTest`; a module writing another module's tables fails `ModularityTest`; no new compiler warnings and Spotless clean. Dependencies: T-002 (DONE), no open question.
- Baseline: `./mvnw -B -q clean verify` green (1/1) before any edit.
- Summary: Imported the Spring Modulith BOM at 2.1.1 and added `spring-modulith-starter-core` (compile) and `spring-modulith-starter-test`, plus `archunit-junit5` pinned to 1.4.2. `ModularityTest` runs `ApplicationModules.verify()` and the `Documenter`. `LayerRulesTest` carries nine ArchUnit rules, one per layer row, all with `allowEmptyShould(true)` while the modules are empty.
- Files: `backend/pom.xml`, `backend/src/test/java/com/cryptopilot/architecture/ModularityTest.java`, `backend/src/test/java/com/cryptopilot/architecture/LayerRulesTest.java`
- Tests: 11 added; suite 12/12; coverage still not measurable (test-only classes, so the bundle stays empty and the gates stay vacuous)
- BR/UC/NSF covered: none — architecture task. `check_traceability.py` unchanged at 0/61.
- Decisions: none new. D-03 was already APPROVED and is now enforced by tests; no D/Q/A item was settled by this task.
- Open questions: none new. Q-08 still blocks T-004 and T-005.
- Next: T-008 (BE1). T-009 (DO) stays blocked on T-004, which is blocked on Q-08.
- Commits: 683bec3 build(common): add spring modulith and archunit for architecture tests · 7fbb2e0 test(common): verify module boundaries with spring modulith · c2a5bbb test(common): enforce layer rules with archunit

**Deviations**
- The T-003 block called `spring-modulith-starter-core` "BOM-managed". It is not: the Spring Boot 4.1.1 BOM contains no Modulith entry. Spring Initializr pairs Boot 4.1.1 with Spring Modulith **2.1.1**, imported through `spring-modulith-bom`, so `spring-modulith.version` is declared in `<properties>` like every other extra version. No ADR was needed — ADR-002 already says extra versions live in the parent POM properties.
- ArchUnit was pinned to **1.4.2**, the version `spring-modulith-core` already brings transitively, rather than the newest release, so only one ArchUnit sits on the classpath.
- The block listed five layer rules as examples but asked for "one rule per row of TD 3.1". Nine rules were written (controller, service, repository, entity, dto, calculator, client, job, event). The tenth row, `config`, has "other modules' internals" as its only restriction, which is exactly what `ModularityTest` checks — writing a weak ArchUnit near-duplicate would have been misleading, so the mapping is documented in the test's Javadoc instead.

**Proof the rules bite** (violations created locally, confirmed failing, then deleted — never committed)
- `com.cryptopilot.trading.calculator.TempBadCalculator` importing `org.springframework.stereotype.Component` → `LayerRulesTest.calculators_arePureJava` failed.
- `com.cryptopilot.trading.service.TempTradingService` referencing `com.cryptopilot.journal.repository.TempJournalRepository` → `ModularityTest` failed with "Module 'trading' depends on non-exposed type com.cryptopilot.journal.repository.TempJournalRepository within module 'journal'". This is the "a module writes another module's tables" criterion: a repository is internal, so the access is rejected at the module boundary.

**Follow-ups for later sessions**
- Drop `allowEmptyShould(true)` from a rule once its layer has real classes — first candidates are `entity`, `dto` and `calculator` after T-008 and T-005.
- Adding `spring-modulith-starter-core` put Modulith autoconfiguration on the production classpath. The event publication registry (D-08, ADR-010) needs `spring-modulith-starter-jpa` and a schema; that belongs to T-005/T-056, not here.
- `spring-modulith-apt` arrives as a compile dependency but never runs, because `annotationProcessorPaths` lists Lombok only. If module metadata is wanted later, add it there deliberately.

### 2026-09-19 – T-002 Backend Maven project (Java 21 + Spring Boot 4.1), build plugins and liveness
- Result: DONE
- Summary: Switched the repository configuration from .NET to Java/Maven, then generated the backend Maven project with Spring Initializr on **Spring Boot 4.1.1** (the latest 4.1.x release; 4.1.2 is still a snapshot), Java 21, groupId `com.cryptopilot`, artifact `cryptopilot-backend`, dependencies web MVC, actuator, validation and Lombok only. Added the compiler (`release 21`, `-parameters`, `-Xlint:all,-processing`, `failOnWarning`), Spotless (Palantir Java Format) and JaCoCo (BUNDLE line ≥ 0.70, `com.cryptopilot.*.calculator*` line ≥ 0.90, application class excluded) plugins, the three profile YAML files and the liveness test.
- Files: `backend/pom.xml`, `backend/mvnw`, `backend/mvnw.cmd`, `backend/.mvn/wrapper/`, `backend/src/main/java/com/cryptopilot/CryptoPilotApplication.java`, `backend/src/main/resources/application{,-dev,-prod}.yml`, `backend/src/test/java/com/cryptopilot/LivenessEndpointTest.java`, `.editorconfig`, `.gitattributes`, `.gitignore`, `README.md`, `deploy/.env.example`, `.github/pull_request_template.md`
- Tests: 1 added; suite 1/1; coverage not measurable yet (the only class is the excluded application class, so the JaCoCo gates pass on an empty bundle)
- BR/UC/NSF covered: none (infrastructure task)
- Decisions: D-02 and D-03 moved to APPROVED; A-08 and Q-03 resolved
- Open questions: none new; Q-08 still blocks T-004 and T-005
- Next: T-003 (BE1). T-008 (BE1) is unblocked by this task; T-004 (DO) now waits only on Q-08.
- Commits: 521caf8 chore: switch repository configuration to java · a896818 build(common): add spring boot maven project and build plugins · 35f4735 test(common): add liveness endpoint test

**Notes for the next session**
- **JaCoCo `haltOnFailure` was NOT deferred.** The `check` goal passes on its own with zero measurable classes ("Analyzed bundle with 0 classes. All coverage checks have been met."), so the gates are live at their real thresholds from now on. T-008 does not need to re-enable anything — but the first real class it adds must come with tests or `verify` will start failing on the 0.70 bundle rule.
- Spring Boot 4 renamed and split several artifacts. `spring-boot-starter-web` is now **`spring-boot-starter-webmvc`**, and there is no single `spring-boot-starter-test`: Initializr generates **`spring-boot-starter-webmvc-test`**, `spring-boot-starter-actuator-test` and `spring-boot-starter-validation-test`. `@AutoConfigureMockMvc` moved from `org.springframework.boot.test.autoconfigure.web.servlet` to **`org.springframework.boot.webmvc.test.autoconfigure`**.
- The Phase 0 handover expected six already-modified configuration files; the working tree was clean, so the .NET → Java switch was made in this session before committing it.

### 2026-09-19 — Local tooling and repository starter (no task id)
- Result: DONE
- Summary: Made the documents local-only (setup scripts writing `.git/info/exclude`), added `pre-commit` and `commit-msg` hooks that block local-only files, `.env` files, AI attribution and non-Conventional subjects, Claude Code local settings with attribution disabled, `/start-task` and `/end-session` commands, the local traceability checker, and the committed repository starter files.
- Files: `docs/tools/`, `.claude/`, `CLAUDE.md` section 9, `README.md`, `.gitignore`, `.gitattributes`, `.editorconfig`, `.github/`, `deploy/`
- Tests: hook behaviour verified in a scratch repository (see package notes)
- BR/UC/NSF covered: none
- Decisions: D-15
- Open questions: Q-08
- Next: T-001
- Commits: —

### 2026-09-19 — Documentation baseline (no task id)
- Result: DONE
- Summary: Produced the SRS (Report 3 v1.0), the logical model (38 entities), the technical design (architecture, folder structure, patterns, algorithms, test strategy), ADR-001 … ADR-012, the AI operating rules, this state file and the traceability seed.
- Files: `docs/srs/`, `docs/design/`, `docs/adr/`, `docs/test/traceability.csv`, `CLAUDE.md`, `CURRENT_STATE.md`, `README.md`
- Tests: none (documentation only); traceability seeded with 175 rows, all `NOT_COVERED`
- BR/UC/NSF covered: specification only, no implementation
- Decisions: D-01 … D-14 recorded; D-02 … D-09 awaiting approval
- Open questions: Q-01 … Q-07
- Next: T-001
- Commits: —

---

## 10. Risks

| ID | Risk | Impact | Likelihood | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | Matching engine correctness (races, restart replay) is the hardest part and sits on the critical path | High | Medium | Property-based and replay tests in T-043; BE1 owns it; start in S4 with a buffer | BE1 |
| R-02 | Binance rate limits or IP restrictions block ingestion | High | Medium | Respect request weights (T-017), cache aggressively, keep a recorded dataset for demos | BE2 |
| R-03 | Setup score stays unapproved and blocks P3 | Medium | High | Q-01 decided before S2 ends; the calculator is versioned so a formula change is additive | BE1 |
| R-04 | Payment sandbox instability close to the demo | Medium | Medium | Adapters behind an interface with a fake gateway for E2E; reconciliation path tested (T-070) | BE1 |
| R-05 | Tết holiday reduces capacity in S9 | Medium | Certain | Only parallel work (P11, P12) planned there | Team |
| R-06 | Mobile app squeezed into one sprint | Medium | Medium | Mobile scope limited to the screens listed in SRS 3.1.1; T-090 decision taken early | FE |
| R-07 | LLM cost or quota overrun | Low | Medium | Daily quota per package (BR-50), caching, sandbox key limits | DO |
| R-08 | Scope creep from "nice to have" features | Medium | Medium | Anything outside the SRS needs a new task row and a Decisions entry | BE1 |

---

## 11. Traceability

Kept current as tasks close (`/end-session` step 5). Each row: BR/UC/NSF/SCR id → task id → code namespace → test name. The file is local-only (`docs/test/traceability.csv`), so it is checked locally, not in CI: `python docs/tools/check_traceability.py --write` updates it from test names (`BR28_...`), and `--strict` fails while any BR has no test (run before release, task T-098).

| Source | Count | Covered by tasks |
|---|---|---|
| Business rules BR-01 … BR-61 | 61 | 17 (BR-01, BR-02, BR-03, BR-04, BR-05, BR-06, BR-15, BR-17, BR-21, BR-29, BR-36, BR-37, BR-44, BR-45, BR-46, BR-49, BR-54), as `check_traceability.py` reports them. T-005, T-006 and T-007 cover the database and seed halves; T-010 adds the domain half of BR-01, BR-04, BR-05 and BR-06. **BR-01, BR-02, BR-03 and BR-06 are now proved end to end**, from the endpoint to the row: T-011 added BR-02, T-012 added BR-03 and closed BR-01 in both directions |
| Use cases UC-01 … UC-52 | 52 | 8 (UC-01, UC-02 from T-011; UC-03, UC-05 from T-012; UC-04 from T-013; UC-06 (avatar in T-101), UC-07, UC-08 from T-014), counted by hand from the test names — `check_traceability.py` reads `BR` ids only, so the `UseCase`, `NonScreenFunction` and `Screen` rows of `traceability.csv` stay empty until it learns the other three prefixes |
| Non-screen functions NSF-01 … NSF-18 | 18 | 0 complete; source access for NSF-01, NSF-02 and NSF-04 built and tested in T-017, their jobs still to come |
| Screens SCR-01 … SCR-44 | 44 | 0 |
| Messages MSG01 … MSG45 | 45 | 15 appear in assertions (MSG01 … MSG11, MSG41, MSG43, MSG44, MSG45), also counted by hand. Every one is returned as a code and never as text, so the sentences stay in SRS section 5.3 and the client owns them (TECHNICAL_DESIGN 5.1); MSG39 and MSG43 are named by an `ErrorCode` as the nearest existing message rather than the right one — A-15 and A-17 |
