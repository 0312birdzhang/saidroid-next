F=/tmp/shimtest/libandroid_runtime.so
echo "=== nativeSetDataSize 附近的字符串 ==="
strings $F | grep -n -A2 -B2 "nativeSetDataSize" | head -12
echo "=== 该库里是否有 AssetManager2/ApkAssets 字样 ==="
strings $F | grep -c "ApkAssets\|AssetManager2"
echo "=== libandroidfw 里是否有这些字样 ==="
strings /tmp/shimtest/libandroidfw.so | grep -E "ApkAssets|AssetManager2" | head -5
