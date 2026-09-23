# ADR-007 — Manual mapping with records, limited Lombok, no mapping frameworks

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE decision D-07; TECHNICAL_DESIGN section 1.4

## Context
Tutorials often add ModelMapper, MapStruct and wide Lombok usage. ModelMapper maps by reflection and fails at run time; MapStruct adds an annotation processor and generated code the team must learn to debug; Lombok `@Data` on JPA entities generates equals, hashCode and setters that break entity identity and bypass the business rules.

## Decision
DTOs and events are Java records with static factory methods (`TradingPlanResponse.from(plan)`); mapping is written by hand in the dto package. Lombok is allowed only for `@Getter`, `@NoArgsConstructor(access = PROTECTED)` on entities and `@RequiredArgsConstructor` for constructor injection. Adding a mapping framework requires a new ADR.

## Consequences
Positive: mapping errors surface at compile time; navigation from controller to service to entity is a direct reference; entities keep their invariants because there are no setters.

Negative: more hand-written mapping code; a field added to an entity must be added to the response record explicitly.

## Alternatives considered
MapStruct: acceptable in principle (compile-time) but not needed at this scale; may be reconsidered with an ADR.
ModelMapper: rejected, run-time reflection errors.
Lombok @Data on entities: rejected, breaks JPA identity and business invariants.
