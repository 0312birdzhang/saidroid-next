#!/bin/bash
# Assemble the r79 evidence report (host-side; reads only stats.json/gate.json) from run directories, the functional probe and the
# configuration comparison. Order keeps "Not verified" last.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
OUT=build/evidence/r79
mkdir -p "$OUT"
python3 scripts/perf/render-report.py --label r79 \
  --gate build/perf/scroll-gate-muted-r79c/gate.json \
  --run build/perf/scroll-pulse-handler-r78 \
  --run build/perf/scroll-triple-legacy-r79c \
  --run build/perf/scroll-copy-r79 \
  --run build/perf/scroll-copy-triple-r79 \
  --run build/perf/scroll-swipe-copy-triple-r79c \
  --run build/perf/scroll-copy-touch-r79c \
  --run build/perf/qq-copy-r79 \
  --run build/perf/qq-copy-triple-r79c > /dev/null
python3 scripts/perf/render-functional.py "$OUT/functional.json" > /tmp/func.md
python3 scripts/perf/compare-perf.py --out "$OUT/compare.md" \
  --stages java_compose_getpixels,draw,jni_int_array_copy,ui_thread_total,frame_interval,frame_callback_gap \
  build/perf/scroll-pulse-handler-r78 build/perf/scroll-triple-legacy-r79c \
  build/perf/scroll-copy-r79 build/perf/scroll-copy-triple-r79 > /dev/null
{ sed -n '1,/^## 8\. Not verified/p' "$OUT/report.md" | sed '$d'
  cat /tmp/func.md
  printf '\n## Configuration comparison\n\n'; cat "$OUT/compare.md"
  printf '\n## 8. Not verified\n\n'; sed -n '/^## 8\. Not verified/,$p' "$OUT/report.md" | tail -n +2
} > /tmp/report-r79.md
mv /tmp/report-r79.md "$OUT/report.md"
echo "REPORT $OUT/report.md $(grep -c '' "$OUT/report.md") lines"
