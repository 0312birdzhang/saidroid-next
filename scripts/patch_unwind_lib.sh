#!/bin/bash
echo "=== 用 objcopy 给 libunwind 加符号别名 ==="
cd /tmp && rm -rf uwp && mkdir uwp && cd uwp
cp /usr/local/lib/libunwind-aarch64.so.8.1.0 libunwind_new.so
echo "=== 当前导出 ==="
nm -D libunwind_new.so 2>/dev/null | grep "iterate_phdr" | head -2
echo
echo "=== 创建别名目标文件 ==="
cat > alias.c <<'EOF'
extern void _Uaarch64_set_iterate_phdr_function(void);
void _ULaarch64_set_iterate_phdr_function(void) {
    _Uaarch64_set_iterate_phdr_function();
}
EOF
gcc -shared -fPIC -o alias.so alias.c -L/usr/local/lib -lunwind-aarch64 2>&1 | head -3
echo "=== 合并到 libunwind ==="
gcc -shared -o libunwind_patched.so -Wl,--whole-archive alias.so -Wl,--no-whole-archive 2>/dev/null || cp alias.so libunwind_patched.so
nm -D alias.so 2>/dev/null | grep iterate | head -3
ls -la alias.so 2>/dev/null
