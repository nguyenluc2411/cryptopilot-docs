# ADR-016 — Web UI and test libraries added to the stack

**Status:** Proposed
**Date:** 2026-10-08
**Deciders:** BE1, BE2, FE, DO
**Related:** TECHNICAL_DESIGN 1.3, 11.1; ADR-015; CURRENT_STATE D-91

## Context
TECHNICAL_DESIGN 1.3 lists the web stack as React 18 + TypeScript + Vite, TanStack Query, React Router,
React Hook Form + zod, @stomp/stompjs and TradingView Lightweight Charts, and 11.1 names Vitest and
Testing Library for web tests. `CLAUDE.md` section 4 requires an ADR and a decision entry for any
package outside that list. The web client (ADR-015) started on React 19, which was current when its
repository was created, and its screens must match the Figma design, which uses the IBM Plex Sans and
JetBrains Mono typefaces and the Lucide icon set. Component tests of forms and dialogs need a DOM.

## Decision
The web client uses React 19 instead of React 18, and adds these packages over TECHNICAL_DESIGN 1.3:
Tailwind CSS 4 (`tailwindcss`, `@tailwindcss/vite`) for styling with the Figma colour tokens; `lucide-react` for icons;
`@fontsource/ibm-plex-sans` and `@fontsource/jetbrains-mono` to serve the Figma typefaces from the
application itself instead of a third-party font CDN; `@hookform/resolvers` to connect React Hook Form
to zod; and, for tests only, `jsdom`, `@testing-library/user-event` and `@testing-library/dom` (the peer
of `@testing-library/react`).
TanStack Query, @stomp/stompjs and Lightweight Charts stay in the stack and are added by the first task
that needs them (T-031 realtime prices, T-032 chart); no other UI, state or chart library is added
without a further ADR.

## Consequences
Positive: the screens reproduce the design's type and icons without hand-copied SVGs, fonts load
without a request to an external host, and form and dialog behaviour is tested as a user drives it.

Negative: nine more packages to keep updated in the web repository; Tailwind classes put styling in
the markup, so reviews must check that only the shared colour tokens are used, never literal colours.
The React 19 deviation from TECHNICAL_DESIGN 1.3 must be reflected there (D-91).

## Alternatives considered
Stay on React 18: rejected; nothing in the client depends on 18, and downgrading a running project
gains nothing.
Load the typefaces from Google Fonts: rejected because it adds a third-party request on every page
load and fails offline.
Copy the icons as inline SVG: rejected; dozens of icons across screens would be duplicated and drift
from the design set.
Test components in the default Node environment only: rejected because forms, focus and dialogs
cannot be exercised without a DOM.
