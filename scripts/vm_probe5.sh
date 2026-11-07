echo "=== /tmp/res/cls ==="; ls /tmp/res/cls
echo "=== /tmp/res2/cls ==="; ls /tmp/res2/cls
echo "=== /tmp/base/cls ==="; ls /tmp/base/cls
echo "=== find java sources of these probes ==="
ls -t /tmp/*.java /tmp/*/*.java 2>/dev/null | head -20
