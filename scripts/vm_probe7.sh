echo "=== apks inside android image ==="
find /tmp/and23/arm64-v8a -name "framework-res.apk" -o -name "SystemUI.apk" 2>/dev/null | head
echo "=== image root ==="
ls /tmp/and23/arm64-v8a 2>/dev/null | head
echo "=== multi.jar is class jar? ==="
unzip -l /tmp/fw23/multi.jar 2>/dev/null | head -5
echo "=== framework-res on device image path search ==="
find /tmp/and23 -name "*.apk" 2>/dev/null | head -10
