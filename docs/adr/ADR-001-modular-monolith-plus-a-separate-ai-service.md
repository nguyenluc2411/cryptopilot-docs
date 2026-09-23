# ADR-001 — Modular monolith plus a separate AI Service

**Status:** Accepted
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-01; TECHNICAL_DESIGN section 1.4

## Context
The team has 4 engineers and 26 weeks and must deliver 52 use cases across 12 business areas plus a web app, a mobile app and an admin console. Microservices were considered in the first architecture draft. A per-service database, service discovery, distributed tracing and an event bus would consume a large share of the schedule and of the operating budget, and none of the scaling reasons for microservices apply at the target capacity (1,000 registered users, 200 concurrent).

The AI Assistant is different from the rest of the system: calls to the LLM provider take seconds, are rate limited by the provider, and fail independently of anything else. Running them inside the request path of the monolith would occupy threads and couple availability of the whole product to a third party.

## Decision
CryptoPilot is built as one deployable backend (modular monolith) with strict internal module boundaries, plus one separate stateless AI Service for all LLM traffic. Both run as Docker containers against a single PostgreSQL database that only the backend writes to.

## Consequences
Positive: one solution to build and deploy, one database and one transaction scope, in-process calls instead of network calls, far simpler local development and CI, operating cost within the capstone budget. Module boundaries keep the option of extracting a service later.

Negative: the whole backend scales as one unit and a bad deployment affects every feature. A module boundary is a convention, so it must be enforced mechanically (ADR-003 and the architecture tests) or it erodes.

This holds while the system stays at the capacity in SRS 4.2.3. Beyond that, MarketData and Analysis are the first candidates for extraction, because they are read heavy and have the fewest write dependencies.

## Alternatives considered
Microservices per bounded context: rejected for this team size and schedule; the operational work is not repaid at this scale.
Single monolith with no internal boundaries: rejected because 12 areas developed by 4 people in parallel would couple quickly and make later extraction impossible.
Serverless functions: rejected because the market data streams are long-lived connections, which fits a persistent process, not a function.
