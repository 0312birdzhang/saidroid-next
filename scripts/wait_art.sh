#!/bin/bash
for i in $(seq 1 20); do
  sleep 60
  RUNNING=$(pgrep -f "make -j4" >/dev/null && echo YES || echo NO)
  ERRS=$(grep -c 'error:' /tmp/art-build9.log 2>/dev/null || echo 0)
  OBJS=$(find /tmp/art-build/art-standalone/out -name '*.o' 2>/dev/null | wc -l)
  echo "[$i] running=$RUNNING errors=$ERRS objs=$OBJS"
  if [ "$RUNNING" = "NO" ]; then
    echo "=== 构建结束 ==="
    tail -12 /tmp/art-build9.log
    echo "=== 产物 ==="
    ls -la /tmp/art-build/art-standalone/out/host/linux-x86/bin/ 2>/dev/null | head -10
    break
  fi
done
