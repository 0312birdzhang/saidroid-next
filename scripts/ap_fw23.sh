ls /tmp/fw23
echo "--- cls 条目数 ---"
ls /tmp/fw23/cls 2>/dev/null | head -5
find /tmp/fw23/cls -name "*.class" 2>/dev/null | wc -l
echo "--- 有 Binder.class 吗 ---"
ls -l /tmp/fw23/cls/android/os/Binder.class 2>/dev/null
echo "--- 原始 android-all jar ---"
ls -l /tmp/fw23/*.jar 2>/dev/null
