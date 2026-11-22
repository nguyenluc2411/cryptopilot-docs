# ADR-025 — Web typography: one type scale after Binance, 12 px floor, fonts by role

**Status:** Accepted (owner, 2026-11-22)
**Date:** 2026-11-21, revised 2026-11-22
**Deciders:** BE1, BE2, FE, DO
**Related:** CURRENT_STATE D-161; ADR-016 (IBM Plex Sans and JetBrains Mono); NFR usability and accessibility; T-141
(design foundation), T-139, T-140, T-142, T-144 (web UI redesign waves)

## Context
The web client has no shared type scale. A code check of FE `develop` `e3841a3` (2026-11-22) finds 504 arbitrary
pixel sizes in components (`text-[11px]` 288 times, `text-[10px]` 125, `text-[9px]` 11, down to `text-[7px]`), the
sizes 10.5, 11.5, 12.5 and 13.5 px added by the first redesign waves, an 18 px step used for page titles next to
20, 24 and 30 px titles on other pages, and 101 uppercase letter-spaced labels. A browser check of the 55 routes
on backend `c1803226` finds only IBM Plex Sans and JetBrains Mono, but words set in JetBrains Mono on eight
screens (alert conditions, plan entry and exit labels, journal facts, the subscription price, the home page section
titles). On 2026-11-22 the FE owner reviewed the redesigned screens and found that each page looked like a
different font; the owner chose one convention for the whole web, taken from one reference site (Binance), with a
12 px floor. This replaces the 10.5 px floor of the 2026-11-21 proposal.

## Decision
The web client uses one type scale, Tailwind's own size tokens, on every page; components use no arbitrary pixel
size, no 18 px step (`text-lg`) and no uppercase letter-spaced labels.

| Token | Size / line height | Use |
|---|---|---|
| `text-xs` | 12 / 16 px | Floor. Labels, column headers, badges, timestamps, helper and error text, order books and trade feeds, chart axis labels. |
| `text-sm` | 14 / 20 px | Body text, form fields, buttons. |
| `text-base` | 16 / 24 px | Card, section and dialog titles. |
| `text-xl` | 20 / 28 px | Page titles, key figures (KPI values). |
| `text-2xl` | 24 / 32 px | Large figures (a pair's price header, a package price). |
| `text-3xl`, `text-4xl` | 30 / 36, 36 / 40 px | Hero headings of the public pages only. |

Fonts by role: IBM Plex Sans for every word (titles, labels, sentences, statuses, badges); JetBrains Mono only for
numbers, prices, percentages, times and technical codes (ids, URLs, JSON). A text that mixes both (an entry
label and its price, an alert condition) keeps the words in IBM Plex Sans. Labels keep their sentence case.

Rules: no text below 12 px anywhere, including chart labels set through the chart library's options; text keeps a
4.5:1 contrast at every size. A unit test over the source files fails on an arbitrary pixel size, on `text-lg`, on
an uppercase label and on a chart font size below 12 px.

## Consequences
- Every page reads the same way; the smallest text grows from 7–11 px to 12 px.
- Dense tables and trading panels get taller rows and some screens show fewer rows above the fold; the layout is
  checked for overflow at 360, 768 and 1440 px.
- One sweep over the web client, not one wave per screen, so the guard can hold from its first commit.
- No new dependency: the sizes are Tailwind's default tokens, and the guard is a plain test.

## Alternatives considered
- **A 10.5 px floor with named tokens** (the 2026-11-21 proposal): kept the dense panels denser, but the redesigned
  screens drifted from the others; withdrawn by the FE owner on 2026-11-22.
- **The sizes of the market screen** (10 to 14 px): fewer changes, but keeps sizes below what the reference exchange
  uses and has no rule for titles.
- **An ESLint plugin for class names**: a new dependency (TECHNICAL_DESIGN 1.3, ADR-016) for a check a unit test
  covers.
