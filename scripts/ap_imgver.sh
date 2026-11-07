echo "=== build.prop 全文关键行 ==="
grep -vE "^#|^$" /tmp/and23/arm64-v8a/build.prop | head -40
echo "=== ApkAssets / AssetManager2（O+ 才有）==="
nm -D --defined-only /tmp/shimtest/libandroidfw.so 2>/dev/null | grep -c "ApkAssets\|AssetManager2"
echo "=== libandroid_runtime 里 O+ 才有的符号 ==="
nm -D --defined-only /tmp/shimtest/libandroid_runtime.so 2>/dev/null | grep -cE "Icu|HardwareBuffer|register_android_graphics_Movie"
