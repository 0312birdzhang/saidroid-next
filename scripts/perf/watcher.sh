#!/bin/sh
# background watcher on the phone: log any SailDroid-owned process every 0.5s
log=/tmp/owned-watch.log
: > $log
i=0
while [ $i -lt 600 ]; do
  for p in /proc/[0-9]*; do
    cmd=$(tr '\0' ' ' < $p/cmdline 2>/dev/null)
    exe=$(readlink $p/exe 2>/dev/null)
    case "$exe" in
      /home/art/bin/dalvikvm) echo "$(date +%H:%M:%S.%N) PID=${p#/proc/} EXE=$exe CMD=$cmd" >> $log ;;
      /home/art/apps/*/dalvikvm) echo "$(date +%H:%M:%S.%N) PID=${p#/proc/} EXE=$exe CMD=$cmd" >> $log ;;
    esac
    case "$cmd" in
      *api29-root/lib/runtime.jar*|*api29-root/libexec/saildroid-open*|org.saildroid.manager*|saildroid-supervisor:*) echo "$(date +%H:%M:%S.%N) PID=${p#/proc/} EXE=$exe CMD=$cmd" >> $log ;;
    esac
  done
  i=$((i+1))
  sleep 0.5
done
