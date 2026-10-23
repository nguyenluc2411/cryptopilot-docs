# ADR-022 — Web community read routes follow the session's shell

**Status:** Accepted (FE owner, 2026-10-23)
**Date:** 2026-10-22
**Deciders:** FE
**Related:** D-99 (CF-01a), A-44; SRS 3.1.3, 3.7; CURRENT_STATE D-113; T-065, T-030

## Context
D-99 lets a Guest read the community: the feed, the pinned announcements, a post with its comments,
the discussion of a coin and member pages. The backend opens those reads to anonymous callers. The
web router groups routes by who may open them: the Guest shell for `/`, a protected Trader shell for
every Trader screen, the Admin console. Community routes were Trader routes, and the Guest header
opened the access gate instead of the forum. SRS 3.1.3 still says the forum is Trader-only (A-44
will update it).

## Decision
A route group "read by everyone" holds `/community`, `/community/:postId` and
`/community/members/:memberId`. Its layout picks the shell from the session: the Trader shell for a
signed-in Trader, the Guest shell for a Guest or while the session cannot be checked, the blocked
screen for a locked or banned account, and the usual denial for an Admin (the Admin console keeps
moderation). `/community/new` and `/community/:postId/edit` stay Trader routes. On the read pages a
Guest's like, save, comment, report or New post opens a sign-in invitation that returns to the same
page. The member page has no SCR id and traces to D-99.

## Consequences
One URL serves both audiences, so links shared from the community open for anyone. The Guest
header shows Community as a normal link; News stays behind the access gate. Pages render the same
components for both and hide the Saved and My posts tabs from a Guest (the backend answers MSG44 for
them anyway).

## Alternatives considered
- Separate Guest pages (`/public/community/...`): two URLs per post and duplicated pages.
- Keeping the forum Trader-only: contradicts D-99 and the registered topic.
