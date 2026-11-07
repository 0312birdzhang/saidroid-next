#!/bin/bash
echo "=== 库里实际导出 ==="
nm -D /usr/local/lib/libunwind-aarch64.so.8.1.0 2>/dev/null | grep "iterate_phdr" | head -3
echo
echo "=== 创建别名 shim 库 ==="
cd /tmp && mkdir -p uwalias && cd uwalias
cat > alias.c <<'EOF'
/* 把 _ULaarch64_ 前缀的引用重定向到实际导出的 _Uaarch64_ */
extern void _Uaarch64_set_iterate_phdr_function(void);
void _ULaarch64_set_iterate_phdr_function(void) {
    _Uaarch64_set_iterate_phdr_function();
}
EOF
gcc -shared -fPIC -o libunwind_alias.so alias.c 2>&1 | head -5
ls -la libunwind_alias.so 2>/dev/null
cp libunwind_alias.so /usr/local/lib/ 2>/dev/null
echo "=== 验证 ==="
nm -D /usr/local/lib/libunwind_alias.so 2>/dev/null | grep iterate | head -3
