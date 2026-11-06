# ADR-023 — Mobile client libraries beyond the TECHNICAL_DESIGN stack

**Status:** Proposed
**Date:** 2026-11-06
**Deciders:** BE1, BE2, FE, DO
**Related:** TECHNICAL_DESIGN 1.3, 4.2, 5.3; ADR-008, ADR-012, ADR-016, ADR-019; CURRENT_STATE D-140, D-141; T-088…T-092; SRS 3.1.1, NSF-15

## Context
TECHNICAL_DESIGN 1.3 gives the mobile client Flutter (stable), Riverpod, dio, go_router and
stomp_dart_client, and leaves the chart library to ADR-012. The mobile tasks need more than that:
the refresh token must survive an app restart in protected storage (T-088 "token refresh works after
app restart"; the fe-guide auth chapter already names `flutter_secure_storage`), copy is English and
kept out of the code (A-45), some screens live only on the web and must open there, device settings
such as the indicator toggles of BR-12 are "remembered on the device", money and prices are decimals
everywhere else in the system (ADR-008 on the backend, ADR-019 on the web), and push notifications
with deep links need Firebase Cloud Messaging on the device (NSF-15, T-092). The web recorded its own
additions the same way (ADR-016).

## Decision
The mobile client adds these packages, each with the first task that needs it and nothing else
without its own decision entry:

| Package | Use | First task |
|---|---|---|
| `flutter_secure_storage` | refresh token in the Android Keystore / iOS Keychain; the access token stays in memory | T-088 |
| `flutter_localizations` (SDK) + `intl` | English copy in ARB files; number and date formatting with an explicit locale, never the device default | T-088 |
| `url_launcher` | screens that exist only on the web (register, plan editor, subscription, profile) open in the browser | T-088 |
| `shared_preferences` | device settings: theme, indicator toggles, last tab; never tokens | T-088 |
| `decimal` | prices, quantities and money as decimals parsed from the API's strings; indicators may stay `double` | T-089 |
| `firebase_core`, `firebase_messaging`, `flutter_local_notifications` | push delivery and foreground display (NSF-15) | T-092 |
| `app_links` | deep links from notifications and from the password reset e-mail | T-092 |
| `mocktail` (dev) | test doubles for repositories and data sources | T-088 |

Versions are pinned in `pubspec.lock` of the mobile repository (D-140). The chart package is decided
by ADR-012, not here.

## Consequences
The refresh token is protected by the platform keystore rather than plain preferences, so
"remember me" works across restarts. Every package is maintained by the Flutter team, Google or a
widely used publisher, but each is one more upgrade to follow; the Firebase packages also bring a
`google-services.json` tied to the Android application id, which must therefore be final before
T-092 starts. JSON stays decoded by hand into domain types (no code generation), as on the web, so
no build-runner step is added.

## Alternatives considered
- `shared_preferences` for the refresh token: readable on a rooted device and in backups; rejected for credentials.
- `easy_localization` or a hand-written string map: a second convention beside the SDK's ARB tooling, which `intl` already covers.
- `json_serializable` / `freezed`: code generation for a client that decodes a small set of DTOs by hand on the web; may be revisited if the DTO count grows.
- WebView screens instead of `url_launcher`: keeps the user in the app but duplicates the web session and its storage rules (ADR-021); the browser is simpler and safer.
- `double` for money: rounding errors in P/L and fees; contradicts ADR-008.
