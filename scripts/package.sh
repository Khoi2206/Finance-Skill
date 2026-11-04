#!/usr/bin/env bash
# Đóng gói mỗi skill thành .zip để tải lên Claude.ai / Cowork (Settings → Capabilities → Skills → Upload).
# Dùng: bash scripts/package.sh [thư_mục_ra]   (mặc định ./dist)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/dist}"
mkdir -p "$OUT"
for d in "$ROOT"/core/*/ "$ROOT"/library/*/*/; do
  [ -f "$d/SKILL.md" ] || continue
  name="$(basename "$d")"
  (cd "$(dirname "$d")" && zip -qr "$OUT/$name.zip" "$name" -x '*.DS_Store')
done
echo "Đã tạo $(ls "$OUT"/*.zip | wc -l) file zip trong $OUT"
