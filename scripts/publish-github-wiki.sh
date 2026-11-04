#!/usr/bin/env bash
set -euo pipefail
mode="${1:-publish}"
[[ "$mode" == "publish" || "$mode" == "--dry-run" ]] || { echo "Usage: bash scripts/publish-github-wiki.sh [--dry-run]" >&2; exit 2; }
root="$(git rev-parse --show-toplevel)"; cd "$root"
test -f docs/wiki/Home.md
temp="$(mktemp -d)"; trap 'rm -rf "$temp"' EXIT
git clone --quiet "https://github.com/nyameko/quantum-platform.wiki.git" "$temp/wiki"
find docs/wiki -maxdepth 1 -name '*.md' -type f -print0 | while IFS= read -r -d '' file; do cp "$file" "$temp/wiki/$(basename "$file")"; done
git -C "$temp/wiki" add -- '*.md'
git -C "$temp/wiki" status --short
git -C "$temp/wiki" diff --cached --quiet && { echo "No changes"; exit 0; }
git -C "$temp/wiki" diff --cached --stat
[[ "$mode" == "--dry-run" ]] && { echo "Dry run only"; exit 0; }
git -C "$temp/wiki" commit -m "docs(wiki): synchronize reviewed source"
git -C "$temp/wiki" push origin HEAD
echo "Published: https://github.com/nyameko/quantum-platform/wiki"
