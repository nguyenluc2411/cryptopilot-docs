# ADR-002 — Java 21 LTS with Spring Boot 4.1 and Maven

**Status:** Accepted
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-02; TECHNICAL_DESIGN section 1.4

## Context
The backend language had to be fixed before any code is written. Earlier drafts named .NET; the team works in Java and Spring Boot, which is also the stack taught in the programme, so Java removes a learning cost for all four members. Within Java, the Spring Boot line must be supported for the whole project (09/2026 to 03/2027): Spring Boot 3.5 reached open-source end of life on 30 June 2026 and 4.0 reaches it on 31 December 2026, in the middle of the project. Spring Boot 4.1 (June 2026) is supported until about July 2027 and runs on Java 17 to 26.

## Decision
The backend uses Java 21 LTS (Eclipse Temurin) and Spring Boot 4.1.x — pinned to 4.1.1 in T-002 — built with Maven through the Maven Wrapper committed in `backend/`. Library versions come from the Spring Boot BOM; extra versions are declared once in the parent POM properties. Virtual threads are enabled.

## Consequences
Positive: the team's existing Java and Spring knowledge applies directly; the Spring ecosystem covers every need of the design (JPA, Security, WebSocket, scheduling, Modulith); support covers the whole project; the wrapper removes local Maven installation.

Negative: Spring Boot 4 is recent, so some tutorials and third-party starters still target Boot 3 and need checking before use (Jackson 3, Spring Framework 7 changes). Java 21 instead of 25 gives up a few newer language features, accepted for wider tool compatibility on the team's machines.

Requires: every new dependency is checked for Spring Boot 4 compatibility before it is added (CLAUDE.md section 4).

## Alternatives considered
.NET 10: rejected, the team's working language is Java.
Spring Boot 3.5: rejected, open-source support ended on 30 June 2026.
Spring Boot 4.0: rejected, support ends on 31 December 2026, mid-project.
Gradle: rejected in favour of Maven, which the team knows and which most course material uses.
Java 25: acceptable, but Java 21 was chosen for compatibility with tools already installed.
