F=/tmp/shimtest/libandroidfw.so
echo "=== ApkAssets / AssetManager2 相关符号（前 20）==="
nm -D --defined-only -C $F 2>/dev/null | grep -E "ApkAssets|AssetManager2" | head -20
echo "=== libandroid_runtime 里 O+ 标志 ==="
nm -D --defined-only -C /tmp/shimtest/libandroid_runtime.so 2>/dev/null | grep -E "ApkAssets|AssetManager2|register_android_content_AssetManager2" | head -5
echo "=== 各库文件日期（zip 内 mtime）==="
ls -l /tmp/and23/libs/lib64/libandroidfw.so /tmp/and23/libs/lib64/libandroid_runtime.so /tmp/and23/libs/lib64/libhwui.so 2>/dev/null
