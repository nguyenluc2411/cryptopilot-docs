# ADR-005 — Spring WebSocket with STOMP for realtime, Redis as cache only

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-05; TECHNICAL_DESIGN section 1.4

## Context
Prices, candles, indicators, alerts and position status must reach web and mobile clients within seconds (SRS 4.2.3). Both clients need the same protocol, and the deployment is a single backend instance on one VPS.

## Decision
Realtime delivery uses Spring WebSocket with the STOMP sub-protocol and the simple in-memory broker, with public topics per pair and user destinations for personal events. Clients use @stomp/stompjs (web) and stomp_dart_client (Flutter). Redis stores the latest prices only; it is not a message bus and not a source of truth.

## Consequences
Positive: first-class Spring support, destination-based routing, user destinations and authentication through the same JWT; maintained client libraries for both front ends. Losing Redis costs a cache warm-up, not data.

Negative: the simple broker lives in the backend process, so a second backend instance would need a broker relay (RabbitMQ STOMP), deliberately not configured.

Requires: no business state is kept only in Redis or in the broker.

## Alternatives considered
Raw WebSocket handlers: rejected, subscription routing, heartbeats and user targeting would be written by hand.
Server-sent events: rejected, one-directional and weaker mobile support.
Client polling: rejected, it cannot meet the latency targets at 200 concurrent users.
