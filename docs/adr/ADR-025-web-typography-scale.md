# ADR-025 — Web typography scale with a 10.5 px floor

**Status:** Proposed
**Date:** 2026-11-21
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE D-161; ADR-016 (IBM Plex Sans and JetBrains Mono); NFR usability and accessibility; T-141
(design foundation), T-139, T-140, T-142, T-144 (web UI redesign waves)

## Context
The web client has no shared type scale. A code check of FE `develop` `6a0d694` (2026-11-21) finds 470
arbitrary pixel sizes in components: `text-[11px]` 283 times, `text-[10px]` 131, `text-[9px]` 12, `text-[8px]` 4
and `text-[7px]` once, next to Tailwind's `text-xs` (363) and `text-sm` (144). Labels, badges and table cells
therefore differ from screen to screen, and some text is too small to read on a phone or a high-resolution
screen. The UI redesign waves (T-139…T-144) need one scale to build on, and the FE owner set the floor on
2026-11-21: 10.5 px is the smallest size anywhere, a floor and not a default, and data tables must stay readable.

## Decision
The web client uses one named type scale, defined once as theme tokens in the global stylesheet and used
through utility classes; components do not use arbitrary pixel sizes.

| Token | Size / line height | Use |
|---|---|---|
| `micro` | 10.5 / 14 px | Floor. Uppercase column headers and labels (tracking ≥ 0.06em, weight ≥ 500), badges, chart axis ticks. Never body text or table cells. |
| `caption` | 11.5 / 16 px | Secondary lines, helper text, timestamps; dense market feeds (order book, recent trades) only. |
| `table` | 12.5 / 18 px | Table cells and list rows; numbers in JetBrains Mono with tabular figures, right-aligned. |
| `body-sm` | 13 / 20 px | Compact body text, form labels. |
| `body` | 14 / 22 px | Default body text (the current base size). |
| `title-sm` | 16 / 24 px | Card and section titles. |
| `title` | 20 / 28 px | Page titles. |
| `figure` | 22 / 28 px | Key figures (KPI values), JetBrains Mono. |
| `display` | 28–40 px | Hero headings of the public pages only. |

Rules: no text below 10.5 px, including chart labels set through the chart library's options; table cells use
`table` or larger, never `micro` or `caption`; text keeps a 4.5:1 contrast at every size of this scale. A unit test
in the repository fails on any size below 10.5 px and on any new arbitrary pixel size; the existing ones are
listed as a baseline that may only shrink, and each redesign wave removes those of the screens it touches.

## Consequences
- Screens read the same way, and the smallest text grows from 7–10 px to 10.5 px.
- Dense tables get taller rows (12.5 px cells); some screens show fewer rows above the fold.
- Order books and trade feeds keep `caption` (11.5 px) to stay dense; this is the only exception for data.
- The migration is per screen, inside each redesign wave, not one sweep, so files shared with teammates change
  in few commits. Until a screen's wave runs, its old sizes stay in the baseline.
- No new dependency: tokens are Tailwind theme values, and the guard is a plain test over the source files.

## Alternatives considered
- **Keep Tailwind's default scale only** (`text-xs` 12 px and up): no 10.5 or 11.5 steps for the dense trading
  panels, so components would keep adding arbitrary sizes.
- **A floor of 12 px**: rejected by the FE owner (2026-11-21); too large for column headers and badges in the
  trading panels.
- **An ESLint plugin for class names**: a new dependency (TECHNICAL_DESIGN 1.3, ADR-016) for a check a unit test
  covers.
