F=/tmp/shimtest/libandroidfw.so
echo "=== addDefaultAssets 头部 ==="
objdump -d --start-address=0x19c34 --stop-address=0x19c90 $F 2>/dev/null | tail -30
echo "=== .rodata 里 AssetManager 用的路径串 ==="
strings -t x $F | grep -E "framework-res.apk|framework/|/system/" | head -10
