---
description: Start a work session on the NEXT task (or the task id given as argument)
argument-hint: "[T-xxx]"
---

Start a work session following CLAUDE.md exactly.

Task: $ARGUMENTS (if empty, use the task marked `NEXT` in CURRENT_STATE.md).

0. **Pull both repositories before reading anything.** `./docs.sh pull` (Windows: `.\docs.ps1 pull`) and
   `git pull`. The documents live in a second repository over this same folder, so without the first one
   CURRENT_STATE.md is whatever this machine last saw — a `NEXT` marker somebody already moved, a task
   already finished, decisions and open questions that have since changed. Everything below is read out of
   that file, so a stale copy makes the whole session wrong rather than slightly out of date. If the pull
   conflicts, resolve it before starting: see docs/BOOTSTRAP.md.

1. Read CLAUDE.md, then CURRENT_STATE.md sections 3–8. Confirm that every dependency of the task is `DONE` and that no `PENDING` alignment item or `OPEN` question in its "Blocks" column blocks it. If it is blocked, stop and report which item blocks it.
2. Read only the TECHNICAL_DESIGN sections, SRS ids and logical model parts the task references.
3. Do the mandatory codebase analysis of CLAUDE.md section 2 and print the 5–10 line summary, including the test baseline.
4. Set the task status to `WIP` in CURRENT_STATE.md.
5. Implement, test and document the task until the Definition of Done (CLAUDE.md section 6) holds. Do not ask for confirmation between phases.
6. Commit locally with Conventional Commits, one logical change per commit, no attribution, no local-only files. Do not push.
7. Finish with /end-session.
