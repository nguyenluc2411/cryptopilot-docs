# ADR-009 — Application-generated UUID v7 primary keys

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-09; TECHNICAL_DESIGN section 1.4

## Context
Keys must be unique, safe to expose in URLs and cheap to index on tables that grow to millions of rows. Sequential integers leak volume and are enumerable in URLs; random UUID v4 keys fragment B-tree indexes badly at this row count. Java has no built-in UUID v7 generator.

## Decision
Primary keys are UUID v7 generated in `BaseEntity` with `Generators.timeBasedEpochGenerator()` from `com.fasterxml.uuid:java-uuid-generator`. `BaseEntity` implements `Persistable<UUID>` so Spring Data inserts assigned ids without a preceding select. Time-series tables keep composite natural keys (pair, market type, timeframe, open time) instead.

## Consequences
Positive: ids exist before the insert, which events and the outbox need; ordered inserts keep index maintenance cheap; ids are safe in URLs.

Negative: 16 bytes per key instead of 8; one small extra dependency; a UUID v7 embeds its creation time, which is acceptable here.

## Alternatives considered
`bigint` identity: rejected, enumerable and unavailable before insert.
UUID v4 (`UUID.randomUUID()`): rejected, random inserts fragment indexes on the largest tables.
Database-generated UUID: rejected, the application needs the id before the transaction commits.
