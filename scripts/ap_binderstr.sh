echo "=== libandroid_runtime 里 Binder 相关的字符串 ==="
strings /tmp/shimtest/libandroid_runtime.so | grep -n "onBinder\|BinderStrictMode\|forceBinderGc" | head -10
echo "=== 附近上下文 ==="
strings /tmp/shimtest/libandroid_runtime.so | grep -A2 -B2 "onBinderStrictModePolicyChange" | head -12
