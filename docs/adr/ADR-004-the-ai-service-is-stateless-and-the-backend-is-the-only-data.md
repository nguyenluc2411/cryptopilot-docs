# ADR-004 — The AI Service is stateless and the backend is the only database writer

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-04; TECHNICAL_DESIGN section 1.4

## Context
The AI Service is written in Node.js while the backend is Java. If both wrote to the same database, the schema would have two owners, Flyway migrations would have to be coordinated across two languages, and entity mapping would be duplicated. The SRS (NSF-16) describes the AI Service as storing the answer, which creates exactly that problem.

## Decision
The AI Service holds no database client. The backend sends it the active configuration and the context snapshot over the private network, receives the generated text and the token usage, and persists the result itself. The AI Service keeps only in-memory state for rate limiting. SRS alignment item A-06 records the deviation.

## Consequences
Positive: one schema owner, one migration path, no cross-language mapping; the AI Service can be restarted or scaled freely; it is trivial to fake in tests (WireMock).

Negative: one extra network hop per request and the backend must handle queueing and retry bookkeeping.

Requires: the AI Service stays off the public Internet and is reachable only from the backend, authenticated with a shared secret.

## Alternatives considered
AI Service with its own database: rejected, two schema owners.
AI calls inside the Java backend: rejected, LLM latency and provider rate limits are isolated in a separate process (ADR-001).
A managed queue between the two: rejected as unnecessary infrastructure; the event publication registry is enough.
