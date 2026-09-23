# ADR-006 — Scheduled jobs, virtual-thread workers and Modulith events for background work

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-06; TECHNICAL_DESIGN section 1.4

## Context
The system has eighteen non-screen functions of three shapes: fixed schedules (symbol sync, reconciliation, expiry, retention), continuous consumers of market events (streams, indicators, alerts, matching), and durable reactions that must not be lost (backfill after enabling a pair, notification dispatch, AI requests).

## Decision
Fixed schedules use Spring `@Scheduled`. Continuous consumers run on virtual threads reading bounded in-process queues, one consumer per partition where ordering matters. Durable reactions are events handled by `@ApplicationModuleListener`, persisted by the Spring Modulith event publication registry and resubmitted when incomplete.

## Consequences
Positive: no extra server or dashboard product; virtual threads make blocking socket and HTTP code cheap; durable work survives restarts through the registry.

Negative: three mechanisms to understand; the registry adds the `event_publication` table (non-business table, alignment item A-09); there is no job dashboard, so job health is exposed through logs and Actuator.

Requires: every job and listener is idempotent (TECHNICAL_DESIGN section 10), because a unit of work can run twice after a restart.

## Alternatives considered
Quartz or JobRunr for everything: rejected, long-lived stream consumers do not fit a job model and a second scheduling product is not needed.
Kafka or RabbitMQ for durable events: rejected, extra infrastructure for a single backend instance.
Cron in the container: rejected, no retry, no history, no visibility.
