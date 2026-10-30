#!/usr/bin/env bash
#
# sync-install.sh — install the vibe-* skills from this repo into ~/.claude/skills,
# install the goldfish reviewer agents into ~/.claude/agents, and stamp the install
# with the current version.
#
# Usage:
#   scripts/sync-install.sh              # sync HEAD of the current working tree
#   scripts/sync-install.sh v2.0.0       # sync a specific tag (checked out, then restored)
#   SKILLS_DIR=/path scripts/sync-install.sh   # override install target
#   AGENTS_DIR=/path scripts/sync-install.sh   # override the agents target
#
# Safe to re-run. Each vibe-* folder is mirrored with rsync --delete, scoped to that
# folder only — other skills in the target directory are never touched. Agents: only
# files named vibe-gf-*.md are written or removed; other agents are never touched.

set -euo pipefail

# Resolve the repo root from this script's location (works from anywhere).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="${SKILLS_DIR:-$HOME/.claude/skills}"
AGENTS_DIR="${AGENTS_DIR:-$HOME/.claude/agents}"
REF="${1:-}"

command -v rsync >/dev/null 2>&1 || { echo "error: rsync is required" >&2; exit 1; }

cd "$REPO_ROOT"

# Optionally check out a specific ref (tag/branch/commit), restoring the prior ref on exit.
RESTORE_REF=""
if [[ -n "$REF" ]]; then
  if ! git rev-parse --verify --quiet "$REF" >/dev/null; then
    echo "error: ref '$REF' not found in this repo" >&2; exit 1
  fi
  RESTORE_REF="$(git symbolic-ref --quiet --short HEAD || git rev-parse HEAD)"
  trap 'git checkout --quiet "$RESTORE_REF"' EXIT
  echo "→ checking out $REF (will restore $RESTORE_REF on exit)"
  git checkout --quiet "$REF"
fi

VERSION="$(tr -d ' \t\n\r' < "$REPO_ROOT/VERSION")"
COMMIT="$(git rev-parse HEAD)"

mkdir -p "$SKILLS_DIR"

count=0
for d in "$REPO_ROOT"/vibe-*/; do
  [[ -d "$d" ]] || continue
  name="$(basename "$d")"
  rsync -a --delete "$d" "$SKILLS_DIR/$name/"
  count=$((count + 1))
done

# Goldfish reviewer agents (vibe-goldfish). Claude Code loads subagent types from
# ~/.claude/agents, so they must live there, not only inside the skill folder.
mkdir -p "$AGENTS_DIR"
agents=0
for f in "$REPO_ROOT"/vibe-goldfish/agents/vibe-gf-*.md; do
  [[ -f "$f" ]] || continue
  cp "$f" "$AGENTS_DIR/"
  agents=$((agents + 1))
done
# remove goldfish agents this version no longer ships
for f in "$AGENTS_DIR"/vibe-gf-*.md; do
  [[ -f "$f" ]] || continue
  [[ -f "$REPO_ROOT/vibe-goldfish/agents/$(basename "$f")" ]] || rm -f "$f"
done

# Write the version stamp so the install advertises what it is.
cat > "$SKILLS_DIR/.vibe-skill-version.json" <<EOF
{
  "framework": "vibe-skill",
  "version": "$VERSION",
  "tag": "v$VERSION",
  "commit": "$COMMIT",
  "source": "https://github.com/aakashdhar/vibe-skill",
  "synced_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "note": "Version marker for the vibe-* skills in this directory. See repo VERSION / CHANGELOG.md."
}
EOF

echo "✓ synced $count vibe-* skills → $SKILLS_DIR (v$VERSION @ ${COMMIT:0:7})"
echo "✓ installed $agents goldfish reviewer agents → $AGENTS_DIR"
echo "  restart Claude Code to pick up any changes (new agents load at startup)."
echo "  check reviewer isolation: python3 $SKILLS_DIR/vibe-goldfish/scripts/isolation_check.py --live"
