# ADR-021 — Web refresh token kept in sessionStorage

**Status:** Accepted (FE owner, 2026-10-13)
**Date:** 2026-10-13
**Deciders:** BE1, BE2, FE, DO
**Related:** Q-67; TECHNICAL_DESIGN 7.15 (rotation and reuse detection); ADR-015; CURRENT_STATE D-109; T-016, T-030

## Context
`/auth/login` and `/auth/refresh` return both tokens in the JSON body, so the browser must keep the
refresh token where script can read it. Until now the web kept both in memory only (Q-67 open), so a
reload or a new tab signed the Trader out. The safer alternative, an `HttpOnly` cookie set by the
backend, needs backend work (cookie, CSRF, `allowCredentials`) that is not planned.

## Decision
The access token stays in memory only. The refresh token, its expiry and the signed-in email (an
Admin has no profile endpoint to read it back) are kept in the tab's `sessionStorage`, never
`localStorage`: written on sign-in and on every rotation, removed on sign-out,
on a refused refresh (the session ended) and on a password reset. When the app starts with no session
in memory and a stored refresh token that has not expired, it calls `POST /auth/refresh` once and
then reads the identity as after a sign-in. The resume is single-flight: React's strict mode starts
it twice in development, and presenting the same refresh token twice reads as reuse to the server. A failed
network call keeps the stored token for the next start; a refused one removes it.

## Consequences
A reload keeps the Trader signed in; closing the tab ends the session on this device. A script
injected into the page (XSS) can read the refresh token, as it could already use the in-memory access
token; the usual XSS defences (no `dangerouslySetInnerHTML`, escaped content, a strict Content
Security Policy in production) remain the protection. "Duplicate tab" copies `sessionStorage`, so two
tabs hold the same refresh token: the first to refresh rotates it, the other then presents a used
token, and the server's reuse detection revokes the session in both; the Trader signs in again and no
data is exposed. "Remember me" keeps its backend meaning (a longer refresh token) but does not
survive closing the tab. Moving to an `HttpOnly` cookie later changes only the auth adapter and the
token session.

## Alternatives considered
- Memory only (as before): a reload signs the Trader out, which the screens cannot hide.
- `localStorage`: survives closing the browser and is shared by every tab, so a stolen token lasts
  longer and tabs race on rotation; ruled out by the web client rules.
- `HttpOnly` cookie set by the backend: the best protection, but needs backend changes, a CSRF
  decision and credentials in CORS; it remains the target if the backend takes it on.
