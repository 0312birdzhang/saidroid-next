for d in /tmp/res /tmp/res2 /tmp/base /tmp/iso /tmp/ctx; do
  echo "=== $d ==="
  ls -la "$d" 2>/dev/null | head -12
done
