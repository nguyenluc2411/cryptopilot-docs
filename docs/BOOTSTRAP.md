# Bootstrap — setting up a machine

Two repositories share one folder.

| Repository | Holds | Git dir | You use |
|---|---|---|---|
| `cryptopilot_project` | Source code, migrations, compose files | `.git/` | `git` |
| `cryptopilot-docs` (private) | `CLAUDE.md`, `CURRENT_STATE.md`, `.claude/`, `docs/` | `.docs.git/` | `./docs.sh` or `.\docs.ps1` |

The documents are not a branch of the code repository and must never become one. Anybody who opens
the code repository — a supervisor, a reviewer, anyone the link is sent to — would find them there.
They still need real version control, because `CURRENT_STATE.md` is appended to at the end of every
session and a shared drive lets one person's session log silently overwrite another's.

---

## First time on a new machine

```bash
git clone https://github.com/nguyenluc2411/cryptopilot_project.git
cd cryptopilot_project

# The documents, into a second git dir inside the same folder
git clone --bare https://github.com/nguyenluc2411/cryptopilot-docs.git .docs.git
git --git-dir=.docs.git --work-tree=. config status.showUntrackedFiles no
git --git-dir=.docs.git --work-tree=. checkout main

# Now the wrappers exist. Install the hooks and the local-only exclusions.
sh docs/tools/setup-local.sh          # Windows: powershell -ExecutionPolicy Bypass -File docs\tools\setup-local.ps1
```

`status.showUntrackedFiles no` is not optional. Without it every source file in the project shows as
untracked in the documents repository, and the first person who types `add .` commits the backend
into it.

### Check it worked

```bash
git status --short          # must NOT list CLAUDE.md, CURRENT_STATE.md, docs/ or .docs.git
./docs.sh status --short    # must NOT list backend/, web/, mobile/
```

Two clean answers mean the two repositories are looking at their own halves of the folder.

---

## Every session

```bash
./docs.sh pull              # before you start - somebody else may have closed a session
git pull                    # the code

# ... work ...

./docs.sh commit -am "T-014: session log, A-30 raised"
./docs.sh push              # at the end, with the session block written
```

Pulling first is what makes this better than a shared drive rather than the same thing with extra
steps. If two people wrote a session block, git says so and you merge them; a drive would keep one
and lose the other without telling anybody.

---

## When `CURRENT_STATE.md` conflicts

It will, and usually in the session log, because entries go newest-first so two people append to the
same place. The resolution is almost always **keep both blocks, newest first** — they are records of
two different sessions and neither replaces the other. Check afterwards that the task table and the
`NEXT` marker still say one consistent thing, because that part is not append-only.

`docs/srs/CryptoPilot_Report3_SRS.docx` is binary and git cannot merge it. Say in the group chat
before editing it, and pull first.

---

## What goes where

The documents repository refuses to commit anything outside its list — a `pre-commit` hook installed
by `setup-local` rejects the commit and names the path. If you see that message, you meant `git`.

Do not add source files to the documents repository, and do not add documents to the code
repository. The code repository has its own `pre-commit` hook refusing the second mistake, so both
directions fail loudly rather than quietly.

## What is deliberately not synced

Nothing, at the moment. `.claude/settings.local.json` is tracked despite the name: it holds team
policy, not machine settings — attribution off, and the deny rules that stop an agent reaching for
`git add -f`, `--no-verify`, `push --force` or reading `deploy/.env`. Everyone needs it. If a file
ever does become machine-specific, exclude it in the documents repository rather than leaving it
untracked by accident.
