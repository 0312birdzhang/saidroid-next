#!/bin/sh
echo "== comm scan =="
for c in /proc/[0-9]*/comm; do
    n=$(cat "$c" 2>/dev/null) || continue
    case "$n" in
        *lipstick*|*compositor*|*topmost*|*invoker*|*wpe*|*atlantic*) echo "$c -> $n" ;;
    esac
done | head -20
echo "== pid 879665/879675 cmdline (from previous pgrep) =="
for p in 879665 879675; do echo "$p: $(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null || echo gone)"; done
