#!/bin/sh
# Git for the project documents, which live in this same folder but belong to a different
# repository. Run it exactly like git:
#
#   ./docs.sh pull
#   ./docs.sh status
#   ./docs.sh commit -am "T-014: session log"
#   ./docs.sh push
#
# Why a second repository rather than a branch of this one: CLAUDE.md, CURRENT_STATE.md and docs/
# must never appear in the code repository at all, not even on a branch nobody merges - anybody
# opening that repository on GitHub would find them. They still need version history and a real
# merge, because CURRENT_STATE.md is appended to at the end of every session and a shared drive
# would let one person's session log silently overwrite another's.
#
# The two repositories share one working tree and are told apart only by which git dir a command
# names. That is the sharp edge of this arrangement, so two things guard it: this wrapper, so the
# git dir is never typed by hand, and a pre-commit hook in the documents repository that refuses
# any path outside the list it is allowed to track.
#
# Setup on a new machine: docs/BOOTSTRAP.md

set -e

root=$(cd "$(dirname "$0")" && pwd)

if [ ! -d "$root/.docs.git" ]; then
    echo "No .docs.git in $root - see docs/BOOTSTRAP.md" >&2
    exit 1
fi

exec git --git-dir="$root/.docs.git" --work-tree="$root" "$@"
