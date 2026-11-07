#!/bin/sh
echo "== total procs: $(ls -d /proc/[0-9]* 2>/dev/null | wc -l)"
echo "== comm list (sorted, first 40) =="
for c in /proc/[0-9]*/comm; do cat "$c" 2>/dev/null; done | sort | uniq -c | sort -rn | head -40
echo "== cmdline containing display/compositor/wayland =="
for d in /proc/[0-9]*; do
    cl=$(tr '\0' ' ' < "$d/cmdline" 2>/dev/null)
    case "$cl" in
        *lipstick*|*compositor*|*invoker*|*topmost*) echo "${d#/proc/}: $cl" ;;
    esac
done | head -10
