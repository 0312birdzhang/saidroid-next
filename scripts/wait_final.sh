#!/bin/bash
for i in $(seq 1 25); do
  sleep 60
  R=$(pgrep -f "make -j4" >/dev/null && echo YES || echo NO)
  E=$(grep -c 'error:' /tmp/art-build11.log 2>/dev/null || echo 0)
  O=$(find /tmp/art-build/art-standalone/out -name '*.o' 2>/dev/null | wc -l)
  echo "[$i] running=$R err=$E obj=$O"
  if [ "$R" = "NO" ]; then
    echo "=== 结束 ==="
    grep -E "error:" /tmp/art-build11.log 2>/dev/null | head -5
    echo "--- 产物 ---"
    ls -la /tmp/art-build/art-standalone/out/host/linux-x86/bin/ 2>/dev/null
    break
  fi
done
