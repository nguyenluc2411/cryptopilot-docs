---
description: Close the work session — verify, update CURRENT_STATE.md and check git hygiene
---

Close the current work session following CLAUDE.md sections 6, 8 and 9.

1. Run the full test suite and the traceability check (`python docs/tools/check_traceability.py`). Record passed/total and coverage.
2. If the Definition of Done does not hold, set the task to `PARTIAL` or `BLOCKED` and add the reason to "Open Questions"; never mark it `DONE`.
3. Append the session block of CLAUDE.md section 8 to CURRENT_STATE.md section 9 (newest first).
4. Update the task status, the phase counts and percentage in section 3, move the `NEXT` marker to the next task whose dependencies are all `DONE`, and update "Last updated" and "Next task" at the top.
5. Update `docs/test/traceability.csv` for every BR/UC/NSF the task covered (task id, namespace, test name, status `COVERED`).
6. Run `git status --short` and `git log --oneline -n 10`. Confirm that no local-only file is tracked or staged and that no commit message contains attribution. Report the result.
7. Print a 5-line summary: task, result, tests, next task, anything the team must decide.
