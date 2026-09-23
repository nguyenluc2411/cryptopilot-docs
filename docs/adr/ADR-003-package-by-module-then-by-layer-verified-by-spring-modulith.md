# ADR-003 — Package by module then by layer, verified by Spring Modulith and ArchUnit

**Status:** Accepted
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-03; TECHNICAL_DESIGN section 1.4

## Context
Inside one deployable backend, the risk is that business rules leak into controllers and repositories, and that twelve areas developed in parallel by four people become entangled. The team is used to the controller / service / repository / model structure, and the 61 business rules of the SRS must sit in code that can be unit tested without a database, a network or a clock.

## Decision
Each module is a direct sub-package of `com.cryptopilot` (auth, user, market, watchlist, trading, journal, community, news, ai, billing, notification, admin, plus the open shared module common). Inside a module the familiar layer packages are used — controller, service, repository, entity, dto — plus calculator (pure business formulas), client (external adapters), job (schedulers and workers), event and config where needed. A module's public API is the set of classes in its root package plus its event package; all other packages are internal. Spring Modulith verifies module boundaries and cycles; ArchUnit verifies the layer rules inside modules.

## Consequences
Positive: the structure the team already knows, grouped so that one feature's files sit together; business formulas in calculator packages are pure Java and trivially testable; boundaries are checked by tests, not by review alone; a module can later be extracted along its package.

Negative: cross-module calls need an explicit API class instead of injecting any service; the rules add two test classes that must stay green.

Requires: ModularityTest and LayerRulesTest run in every build.

## Alternatives considered
Package by layer (controller/, service/, repository/ at the top): rejected, each folder would hold 30–50 unrelated files and module boundaries could not be checked.
Maven multi-module Clean Architecture (domain, application, infrastructure, api): rejected as more build complexity than a 4-person team needs; the same rules are enforced by tests.
No enforcement: rejected, boundaries erode silently.
