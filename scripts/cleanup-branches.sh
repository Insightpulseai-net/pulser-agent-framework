#!/usr/bin/env bash
# Branch cleanup script for pulser-agent-framework
# Deletes merged feature/* and claude/* branches (except keep-list)
set -euo pipefail

PRIMARY_BRANCH="main"

# Branches to keep (add any active work branches here)
KEEP_BRANCHES=(
  "main"
  "claude/data-engineering-workbench-01Pk6KXASta9H4oeCMY8EBAE"
  "claude/implement-todo-item-O1U6u"
  "feat/odoo-18-oca-automation"
)

is_kept() {
  local b="$1"
  for kb in "${KEEP_BRANCHES[@]}"; do
    [[ "$b" == "$kb" ]] && return 0
  done
  return 1
}

echo "=== Branch Cleanup Script ==="
echo "Primary branch: $PRIMARY_BRANCH"
echo

# Fetch and prune
git fetch --all --prune
git checkout "$PRIMARY_BRANCH"
git pull origin "$PRIMARY_BRANCH"

echo
echo "=== Deleting merged feature/* branches ==="
for b in feature/integration-layer feature/m365-ui feature/ppm-workflows; do
  if git ls-remote --exit-code origin "refs/heads/$b" >/dev/null 2>&1; then
    echo "Deleting: $b"
    git push origin --delete "$b" || echo "  Failed to delete $b"
  else
    echo "Already gone: $b"
  fi
done

echo
echo "=== Checking for merged claude/* branches ==="
MERGED_BRANCHES=$(git branch -r --merged "origin/$PRIMARY_BRANCH" | sed 's/^[ *]*//')

while read -r rb; do
  [[ -z "$rb" ]] && continue
  name="${rb#origin/}"

  # Skip non-claude branches (handled above)
  if [[ "$name" != claude/* ]]; then
    continue
  fi

  if is_kept "$name"; then
    echo "Keeping: $name"
    continue
  fi

  echo "Deleting merged: $name"
  git push origin --delete "$name" || echo "  Failed to delete $name"
done <<< "$MERGED_BRANCHES"

echo
echo "=== Remaining remote branches ==="
git ls-remote --heads origin | awk '{print $2}' | sed 's#refs/heads/##' | sort

echo
echo "=== Done ==="
