# ADR-010 — Transactional outbox through the Spring Modulith event publication registry

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-10; TECHNICAL_DESIGN section 1.4

## Context
Several actions must change the database and also cause an external side effect: an alert fires and an email and a push must go out; an order is paid and a receipt must be sent; an AI question is accepted and a provider call must follow. Calling the provider inside the transaction lets a slow or failing provider roll back business data; calling it after the commit loses the side effect on a crash.

## Decision
Services publish domain events with `ApplicationEventPublisher`. The Spring Modulith event publication registry (JDBC) stores each publication in the `event_publication` table in the same transaction as the business change. Listeners annotated `@ApplicationModuleListener` run asynchronously after commit, in their own transaction; a publication is marked complete only when its listener succeeds. Incomplete publications are resubmitted on restart and by a scheduled job.

## Consequences
Positive: business data and the intent to act commit atomically; a provider outage delays delivery instead of losing it; no custom outbox table or processor to write.

Negative: delivery is at-least-once, so every listener must tolerate a duplicate; the registry table must be created by a Flyway migration and cleaned by retention (NSF-17).

Requires: a natural idempotency key on each side effect (notification id, order code, AI message id).

## Alternatives considered
Hand-written outbox table and processor: rejected, the registry provides the same guarantee.
Direct call inside the transaction: rejected, external latency and failure would abort business transactions.
A message broker: rejected as unnecessary infrastructure for a single backend instance (ADR-001).
