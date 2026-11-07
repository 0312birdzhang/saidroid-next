#!/bin/sh
echo "== ps matching lipstick/sailfish/wpe =="
ps -eo pid,comm 2>/dev/null | grep -Ei 'lipstick|compositor|wpe' | head
echo "== ps -A head count=$(ps -A 2>/dev/null | wc -l)"
echo "== topmost? =="
ps -eo pid,comm 2>/dev/null | grep -Ei 'topmost|invoker' | head -3
echo "== pgrep -f lipstick: $(pgrep -f lipstick | tr '\n' ' ')"
