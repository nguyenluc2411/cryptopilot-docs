# -*- coding: utf-8 -*-
"""Generates docs/adr/*.md from the decision set of TECHNICAL_DESIGN 1.4."""
import os

TEMPLATE = """# ADR-000 — Template

**Status:** Proposed | Accepted | Superseded by ADR-xxx
**Date:** YYYY-MM-DD
**Deciders:** BE1, BE2, FE, DO
**Related:** SRS ids, TECHNICAL_DESIGN sections, CURRENT_STATE decision id

## Context
What forces the decision: requirement, constraint, team capacity, deadline, risk.

## Decision
One paragraph, in the present tense, stating what is adopted.

## Consequences
Positive, negative and what becomes harder. Include what has to be true for this to keep working.

## Alternatives considered
Each alternative with the reason it was not chosen.
"""

ADR = {
1: ("Modular monolith plus a separate AI Service", "Accepted", "D-01",
"""The team has 4 engineers and 26 weeks and must deliver 52 use cases across 12 business areas plus a web app, a mobile app and an admin console. Microservices were considered in the first architecture draft. A per-service database, service discovery, distributed tracing and an event bus would consume a large share of the schedule and of the operating budget, and none of the scaling reasons for microservices apply at the target capacity (1,000 registered users, 200 concurrent).

The AI Assistant is different from the rest of the system: calls to the LLM provider take seconds, are rate limited by the provider, and fail independently of anything else. Running them inside the request path of the monolith would occupy threads and couple availability of the whole product to a third party.""",
"""CryptoPilot is built as one deployable backend (modular monolith) with strict internal module boundaries, plus one separate stateless AI Service for all LLM traffic. Both run as Docker containers against a single PostgreSQL database that only the backend writes to.""",
"""Positive: one solution to build and deploy, one database and one transaction scope, in-process calls instead of network calls, far simpler local development and CI, operating cost within the capstone budget. Module boundaries keep the option of extracting a service later.

Negative: the whole backend scales as one unit and a bad deployment affects every feature. A module boundary is a convention, so it must be enforced mechanically (ADR-003 and the architecture tests) or it erodes.

This holds while the system stays at the capacity in SRS 4.2.3. Beyond that, MarketData and Analysis are the first candidates for extraction, because they are read heavy and have the fewest write dependencies.""",
"""Microservices per bounded context: rejected for this team size and schedule; the operational work is not repaid at this scale.
Single monolith with no internal boundaries: rejected because 12 areas developed by 4 people in parallel would couple quickly and make later extraction impossible.
Serverless functions: rejected because the market data streams are long-lived connections, which fits a persistent process, not a function."""),

2: ("Java 21 LTS with Spring Boot 4.1 and Maven", "Accepted", "D-02",
"""The backend language had to be fixed before any code is written. Earlier drafts named .NET; the team works in Java and Spring Boot, which is also the stack taught in the programme, so Java removes a learning cost for all four members. Within Java, the Spring Boot line must be supported for the whole project (09/2026 to 03/2027): Spring Boot 3.5 reached open-source end of life on 30 June 2026 and 4.0 reaches it on 31 December 2026, in the middle of the project. Spring Boot 4.1 (June 2026) is supported until about July 2027 and runs on Java 17 to 26.""",
"""The backend uses Java 21 LTS (Eclipse Temurin) and Spring Boot 4.1.x, built with Maven through the Maven Wrapper committed in `backend/`. Library versions come from the Spring Boot BOM; extra versions are declared once in the parent POM properties. Virtual threads are enabled.""",
"""Positive: the team's existing Java and Spring knowledge applies directly; the Spring ecosystem covers every need of the design (JPA, Security, WebSocket, scheduling, Modulith); support covers the whole project; the wrapper removes local Maven installation.

Negative: Spring Boot 4 is recent, so some tutorials and third-party starters still target Boot 3 and need checking before use (Jackson 3, Spring Framework 7 changes). Java 21 instead of 25 gives up a few newer language features, accepted for wider tool compatibility on the team's machines.

Requires: every new dependency is checked for Spring Boot 4 compatibility before it is added (CLAUDE.md section 4).""",
""".NET 10: rejected, the team's working language is Java.
Spring Boot 3.5: rejected, open-source support ended on 30 June 2026.
Spring Boot 4.0: rejected, support ends on 31 December 2026, mid-project.
Gradle: rejected in favour of Maven, which the team knows and which most course material uses.
Java 25: acceptable, but Java 21 was chosen for compatibility with tools already installed."""),

3: ("Package by module then by layer, verified by Spring Modulith and ArchUnit", "Accepted", "D-03",
"""Inside one deployable backend, the risk is that business rules leak into controllers and repositories, and that twelve areas developed in parallel by four people become entangled. The team is used to the controller / service / repository / model structure, and the 61 business rules of the SRS must sit in code that can be unit tested without a database, a network or a clock.""",
"""Each module is a direct sub-package of `com.cryptopilot` (auth, user, market, watchlist, trading, journal, community, news, ai, billing, notification, admin, plus the open shared module common). Inside a module the familiar layer packages are used — controller, service, repository, entity, dto — plus calculator (pure business formulas), client (external adapters), job (schedulers and workers), event and config where needed. A module's public API is the set of classes in its root package plus its event package; all other packages are internal. Spring Modulith verifies module boundaries and cycles; ArchUnit verifies the layer rules inside modules.""",
"""Positive: the structure the team already knows, grouped so that one feature's files sit together; business formulas in calculator packages are pure Java and trivially testable; boundaries are checked by tests, not by review alone; a module can later be extracted along its package.

Negative: cross-module calls need an explicit API class instead of injecting any service; the rules add two test classes that must stay green.

Requires: ModularityTest and LayerRulesTest run in every build.""",
"""Package by layer (controller/, service/, repository/ at the top): rejected, each folder would hold 30–50 unrelated files and module boundaries could not be checked.
Maven multi-module Clean Architecture (domain, application, infrastructure, api): rejected as more build complexity than a 4-person team needs; the same rules are enforced by tests.
No enforcement: rejected, boundaries erode silently."""),

4: ("The AI Service is stateless and the backend is the only database writer", "Proposed", "D-04",
"""The AI Service is written in Node.js while the backend is Java. If both wrote to the same database, the schema would have two owners, Flyway migrations would have to be coordinated across two languages, and entity mapping would be duplicated. The SRS (NSF-16) describes the AI Service as storing the answer, which creates exactly that problem.""",
"""The AI Service holds no database client. The backend sends it the active configuration and the context snapshot over the private network, receives the generated text and the token usage, and persists the result itself. The AI Service keeps only in-memory state for rate limiting. SRS alignment item A-06 records the deviation.""",
"""Positive: one schema owner, one migration path, no cross-language mapping; the AI Service can be restarted or scaled freely; it is trivial to fake in tests (WireMock).

Negative: one extra network hop per request and the backend must handle queueing and retry bookkeeping.

Requires: the AI Service stays off the public Internet and is reachable only from the backend, authenticated with a shared secret.""",
"""AI Service with its own database: rejected, two schema owners.
AI calls inside the Java backend: rejected, LLM latency and provider rate limits are isolated in a separate process (ADR-001).
A managed queue between the two: rejected as unnecessary infrastructure; the event publication registry is enough."""),

5: ("Spring WebSocket with STOMP for realtime, Redis as cache only", "Proposed", "D-05",
"""Prices, candles, indicators, alerts and position status must reach web and mobile clients within seconds (SRS 4.2.3). Both clients need the same protocol, and the deployment is a single backend instance on one VPS.""",
"""Realtime delivery uses Spring WebSocket with the STOMP sub-protocol and the simple in-memory broker, with public topics per pair and user destinations for personal events. Clients use @stomp/stompjs (web) and stomp_dart_client (Flutter). Redis stores the latest prices only; it is not a message bus and not a source of truth.""",
"""Positive: first-class Spring support, destination-based routing, user destinations and authentication through the same JWT; maintained client libraries for both front ends. Losing Redis costs a cache warm-up, not data.

Negative: the simple broker lives in the backend process, so a second backend instance would need a broker relay (RabbitMQ STOMP), deliberately not configured.

Requires: no business state is kept only in Redis or in the broker.""",
"""Raw WebSocket handlers: rejected, subscription routing, heartbeats and user targeting would be written by hand.
Server-sent events: rejected, one-directional and weaker mobile support.
Client polling: rejected, it cannot meet the latency targets at 200 concurrent users."""),

6: ("Scheduled jobs, virtual-thread workers and Modulith events for background work", "Proposed", "D-06",
"""The system has eighteen non-screen functions of three shapes: fixed schedules (symbol sync, reconciliation, expiry, retention), continuous consumers of market events (streams, indicators, alerts, matching), and durable reactions that must not be lost (backfill after enabling a pair, notification dispatch, AI requests).""",
"""Fixed schedules use Spring `@Scheduled`. Continuous consumers run on virtual threads reading bounded in-process queues, one consumer per partition where ordering matters. Durable reactions are events handled by `@ApplicationModuleListener`, persisted by the Spring Modulith event publication registry and resubmitted when incomplete.""",
"""Positive: no extra server or dashboard product; virtual threads make blocking socket and HTTP code cheap; durable work survives restarts through the registry.

Negative: three mechanisms to understand; the registry adds the `event_publication` table (non-business table, alignment item A-09); there is no job dashboard, so job health is exposed through logs and Actuator.

Requires: every job and listener is idempotent (TECHNICAL_DESIGN section 10), because a unit of work can run twice after a restart.""",
"""Quartz or JobRunr for everything: rejected, long-lived stream consumers do not fit a job model and a second scheduling product is not needed.
Kafka or RabbitMQ for durable events: rejected, extra infrastructure for a single backend instance.
Cron in the container: rejected, no retry, no history, no visibility."""),

7: ("Manual mapping with records, limited Lombok, no mapping frameworks", "Proposed", "D-07",
"""Tutorials often add ModelMapper, MapStruct and wide Lombok usage. ModelMapper maps by reflection and fails at run time; MapStruct adds an annotation processor and generated code the team must learn to debug; Lombok `@Data` on JPA entities generates equals, hashCode and setters that break entity identity and bypass the business rules.""",
"""DTOs and events are Java records with static factory methods (`TradingPlanResponse.from(plan)`); mapping is written by hand in the dto package. Lombok is allowed only for `@Getter`, `@NoArgsConstructor(access = PROTECTED)` on entities and `@RequiredArgsConstructor` for constructor injection. Adding a mapping framework requires a new ADR.""",
"""Positive: mapping errors surface at compile time; navigation from controller to service to entity is a direct reference; entities keep their invariants because there are no setters.

Negative: more hand-written mapping code; a field added to an entity must be added to the response record explicitly.""",
"""MapStruct: acceptable in principle (compile-time) but not needed at this scale; may be reconsidered with an ADR.
ModelMapper: rejected, run-time reflection errors.
Lombok @Data on entities: rejected, breaks JPA identity and business invariants."""),

8: ("BigDecimal precision and rounding policy", "Proposed", "D-08",
"""The graded core of the project is financial arithmetic: position size, risk, reward, liquidation price, fees, funding and realized profit. Binary floating point cannot represent decimal prices exactly, so accumulating fees or funding in `double` produces drift that is visible in a demo and impossible to defend (Bloch 2018, Effective Java, Item 60).""",
"""Prices, quantities, notional values, margins, fees, funding and profit use `BigDecimal` end to end — in entities, in calculators, in the database (`numeric` with the precisions of TECHNICAL_DESIGN 5.4) and in API responses, which serialize them as JSON strings so that JavaScript cannot round them. Divisions use `MathContext.DECIMAL128`; every `setScale` names its `RoundingMode`: quantities down to the step size, prices to the tick size, liquidation distance conservatively. Values are compared with `compareTo`, never `equals`. `double` is permitted only inside indicator mathematics, whose results are display values, never money.""",
"""Positive: reproducible arithmetic; results match the exchange calculators used as test oracles; no rounding surprises between backend, web and mobile.

Negative: `BigDecimal` is slower and more verbose than `double`, and the web and mobile clients must use a decimal library instead of native numbers.

Requires: an ArchUnit rule that forbids `double`/`float` fields in entities and in money calculators (CLAUDE.md section 4).""",
"""`double` throughout: rejected, accumulation drift.
Integer minor units (`long`): rejected because crypto quantities need eight or more decimal places and the scale differs per pair.
`BigDecimal` internally but JSON numbers on the wire: rejected, JavaScript loses precision on parse."""),

9: ("Application-generated UUID v7 primary keys", "Proposed", "D-09",
"""Keys must be unique, safe to expose in URLs and cheap to index on tables that grow to millions of rows. Sequential integers leak volume and are enumerable in URLs; random UUID v4 keys fragment B-tree indexes badly at this row count. Java has no built-in UUID v7 generator.""",
"""Primary keys are UUID v7 generated in `BaseEntity` with `Generators.timeBasedEpochGenerator()` from `com.fasterxml.uuid:java-uuid-generator`. `BaseEntity` implements `Persistable<UUID>` so Spring Data inserts assigned ids without a preceding select. Time-series tables keep composite natural keys (pair, market type, timeframe, open time) instead.""",
"""Positive: ids exist before the insert, which events and the outbox need; ordered inserts keep index maintenance cheap; ids are safe in URLs.

Negative: 16 bytes per key instead of 8; one small extra dependency; a UUID v7 embeds its creation time, which is acceptable here.""",
"""`bigint` identity: rejected, enumerable and unavailable before insert.
UUID v4 (`UUID.randomUUID()`): rejected, random inserts fragment indexes on the largest tables.
Database-generated UUID: rejected, the application needs the id before the transaction commits."""),

10: ("Transactional outbox through the Spring Modulith event publication registry", "Proposed", "D-10",
"""Several actions must change the database and also cause an external side effect: an alert fires and an email and a push must go out; an order is paid and a receipt must be sent; an AI question is accepted and a provider call must follow. Calling the provider inside the transaction lets a slow or failing provider roll back business data; calling it after the commit loses the side effect on a crash.""",
"""Services publish domain events with `ApplicationEventPublisher`. The Spring Modulith event publication registry (JDBC) stores each publication in the `event_publication` table in the same transaction as the business change. Listeners annotated `@ApplicationModuleListener` run asynchronously after commit, in their own transaction; a publication is marked complete only when its listener succeeds. Incomplete publications are resubmitted on restart and by a scheduled job.""",
"""Positive: business data and the intent to act commit atomically; a provider outage delays delivery instead of losing it; no custom outbox table or processor to write.

Negative: delivery is at-least-once, so every listener must tolerate a duplicate; the registry table must be created by a Flyway migration and cleaned by retention (NSF-17).

Requires: a natural idempotency key on each side effect (notification id, order code, AI message id).""",
"""Hand-written outbox table and processor: rejected, the registry provides the same guarantee.
Direct call inside the transaction: rejected, external latency and failure would abort business transactions.
A message broker: rejected as unnecessary infrastructure for a single backend instance (ADR-001)."""),

11: ("Matching engine price source: 1-minute klines plus mark price", "Proposed", "D-11",
"""Simulated fills and exits must be defensible: a trader will compare a fill against the real chart. Using only the last trade price of a tick stream misses levels touched between ticks and cannot be replayed after a restart. The SRS recovery rule (NSF-07) proposes 15-minute candles, which is too coarse — a 15-minute candle can contain both the stop loss and the take profit with no way to order them.""",
"""The engine evaluates entries and exits against the high and low of the `kline_1m` stream and, for futures liquidation, against the mark price stream, as SRS BR-35 requires. After downtime, missing 1-minute klines are fetched by REST and replayed through the same code path as live events. When a stop loss and a take profit fall inside the same candle or replay range, the stop loss is applied first. Alignment item A-04 records the change from the SRS.""",
"""Positive: fills match what the trader sees on the chart; replay and live processing share one implementation, so recovery is testable; the conservative tie-break cannot inflate the win rate, which is the statistic the whole journal feature rests on.

Negative: fills are accurate to one minute, not to the tick; the pessimistic tie-break occasionally reports a loss where reality might have given a win.

Requires: 1-minute klines are ingested and retained for every enabled pair, and the replay test asserts that replay equals live processing.""",
"""Tick stream only: rejected, no replay after downtime and levels between ticks are missed.
15-minute candles for recovery as written in the SRS: rejected, cannot order two levels inside one candle.
Aggregate trade stream: rejected, the volume and storage cost is not repaid by the extra precision at this scale."""),

12: ("Flutter chart library", "Open", "—",
"""The mobile app must draw candlestick charts with indicator overlays, matching the analysis screens of the web app. The web app uses TradingView Lightweight Charts, which has no first-party Flutter package. Candidates differ in licence, maintenance status, indicator support and performance with 500 candles.""",
"""Open. To be decided in phase P14, task T-090, before mobile chart work starts. The evaluation must record: licence and attribution obligation, last release date, indicator overlay support, rendering performance with 500 candles on a mid-range Android device, and whether a WebView wrapper around the web chart is acceptable instead.""",
"""Deferring is safe because no other mobile task depends on the choice: T-088, T-089, T-091 and T-092 are unaffected. Deciding late is a risk only if the evaluation itself slips, which is tracked as risk R-06.""",
"""To be filled in when the decision is made. Include at least one native Flutter package and the WebView option.""")
}

os.makedirs('docs/adr', exist_ok=True)
open('docs/adr/ADR-000-template.md', 'w', encoding='utf-8').write(TEMPLATE)

for n, (title, status, dec, context, decision, consequences, alternatives) in ADR.items():
    slug = title.lower().replace(' ', '-').replace(',', '').replace('.', '').replace(':', '')
    slug = ''.join(ch for ch in slug if ch.isalnum() or ch == '-')[:60].strip('-')
    body = f"""# ADR-{n:03d} — {title}

**Status:** {status}
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision {dec}; TECHNICAL_DESIGN section 1.4

## Context
{context}

## Decision
{decision}

## Consequences
{consequences}

## Alternatives considered
{alternatives}
"""
    open(f'docs/adr/ADR-{n:03d}-{slug}.md', 'w', encoding='utf-8').write(body)

print('written', len(ADR) + 1, 'files')
