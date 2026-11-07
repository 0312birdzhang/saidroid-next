echo "=== 各目录 libhwui 大小 ==="
ls -l /tmp/shimtest/libhwui.so /tmp/and23/biolibs/libhwui.so /tmp/and23/bio2/libhwui.so 2>/dev/null
echo "=== 替身导出的符号 ==="
nm -D --defined-only /tmp/shimtest/libhwui.so 2>/dev/null | wc -l
echo "=== 真实库导出的符号 ==="
nm -D --defined-only /tmp/and23/biolibs/libhwui.so 2>/dev/null | wc -l
echo "=== register_android_view_RenderNode / DisplayListCanvas ==="
nm -D --defined-only /tmp/shimtest/libandroid_runtime.so 2>/dev/null | grep -E "register_android_view_RenderNode|register_android_view_DisplayListCanvas|register_android_view_ThreadedRenderer" | head -5
