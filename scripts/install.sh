#!/usr/bin/env bash
# Cài toàn bộ skill (core + library) vào thư mục skill của Claude Code.
# Dùng: bash scripts/install.sh [thư_mục_đích]   (mặc định ~/.claude/skills)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$HOME/.claude/skills}"
mkdir -p "$DEST"
n=0
for d in "$ROOT"/core/*/ "$ROOT"/library/*/*/; do
  [ -f "$d/SKILL.md" ] || continue
  name="$(basename "$d")"
  rm -rf "$DEST/$name"; cp -R "$d" "$DEST/$name"; n=$((n+1))
done
echo "Đã cài $n skill vào $DEST"
