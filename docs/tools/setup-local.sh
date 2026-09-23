#!/bin/sh
# One-time local setup. Run from the repository root:  sh docs/tools/setup-local.sh
# - keeps the project documents and AI tooling out of git (via .git/info/exclude,
#   which is local to this clone and never committed)
# - installs the commit-msg and pre-commit hooks
# Safe to run again; it rewrites only its own managed block.

set -e

root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "Run this inside the git repository." >&2; exit 1; }
cd "$root"
git_dir=$(git rev-parse --git-dir)
mkdir -p "$git_dir/info" "$git_dir/hooks"
exclude="$git_dir/info/exclude"
touch "$exclude"

# ---- 1. Local-only paths (edit this list if the team decides to publish a file)
block='# >>> cryptopilot-local-only (managed by docs/tools/setup-local)
/CLAUDE.md
/CLAUDE.local.md
/CURRENT_STATE.md
/.claude/
/docs/README.md
/docs/BOOTSTRAP.md
/docs/srs/
/docs/design/
/docs/adr/
/docs/test/
/docs/tools/
# The second git dir that syncs everything above between team members, and its wrappers.
/.docs.git/
/docs.ps1
/docs.sh
# <<< cryptopilot-local-only'

tmp="$exclude.tmp"
sed '/^# >>> cryptopilot-local-only/,/^# <<< cryptopilot-local-only/d' "$exclude" | tr -d '\r' > "$tmp"
printf '%s\n' "$block" >> "$tmp"
mv "$tmp" "$exclude"
echo "[setup] local-only paths written to $exclude"

# ---- 2. Hooks (normalize to LF so they run under Git Bash on Windows too)
hooks_path=$(git config --get core.hooksPath || true)
if [ -n "$hooks_path" ]; then
  echo "[setup] WARNING: core.hooksPath is set to '$hooks_path'; installing hooks there." >&2
  target="$hooks_path"
else
  target="$git_dir/hooks"
fi
mkdir -p "$target"
for h in commit-msg pre-commit; do
  tr -d '\r' < "docs/tools/hooks/$h" > "$target/$h"
  chmod +x "$target/$h"
done
echo "[setup] hooks installed in $target"

# ---- 2b. The documents repository has its own pre-commit, because it shares this working tree
#         and a mistyped command would otherwise stage the whole backend into it.
if [ -d ".docs.git" ]; then
  mkdir -p .docs.git/hooks
  tr -d '
' < docs/tools/hooks/docs-pre-commit > .docs.git/hooks/pre-commit
  chmod +x .docs.git/hooks/pre-commit
  git --git-dir=.docs.git --work-tree=. config status.showUntrackedFiles no
  echo "[setup] documents repository guarded (.docs.git/hooks/pre-commit)"
else
  echo "[setup] no .docs.git yet - see docs/BOOTSTRAP.md to clone the documents repository"
fi

# ---- 3. Check that nothing local-only is already tracked
tracked=$(git ls-files CLAUDE.md CLAUDE.local.md CURRENT_STATE.md .claude docs/README.md docs/srs docs/design docs/adr docs/test docs/tools 2>/dev/null || true)
if [ -n "$tracked" ]; then
  echo "[setup] WARNING: these local-only files are already tracked by git:" >&2
  echo "$tracked" >&2
  echo "[setup] Untrack them (files stay on disk):  git rm -r --cached <path>  then commit." >&2
fi

echo "[setup] done. Verify with: git status --short   (local-only files must not appear)"
