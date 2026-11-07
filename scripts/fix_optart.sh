#!/bin/bash
echo "=== 1. 装 libunwind 1.8.1 到 /opt/art/lib ==="
cp -a /usr/local/lib/libunwind*.so* /opt/art/lib/aarch64-linux-gnu/ 2>/dev/null
ls /opt/art/lib/aarch64-linux-gnu/libunwind* 2>/dev/null | head -3

echo "=== 2. 建别名库 ==="
cat > /tmp/uwalias.c <<'EOF'
extern void _Uaarch64_set_iterate_phdr_function(void);
void _ULaarch64_set_iterate_phdr_function(void) {
    _Uaarch64_set_iterate_phdr_function();
}
EOF
gcc -shared -fPIC -o /opt/art/lib/aarch64-linux-gnu/libunwind_alias.so /tmp/uwalias.c \
  -L/opt/art/lib/aarch64-linux-gnu -lunwind-aarch64 2>&1 | head -3
nm -D /opt/art/lib/aarch64-linux-gnu/libunwind_alias.so 2>/dev/null | grep iterate | head -2

echo "=== 3. 测试 dalvikvm ==="
LD_LIBRARY_PATH=/opt/art/lib/aarch64-linux-gnu:/opt/art/lib \
  /opt/art/bin/dalvikvm -showversion 2>&1 | head -5
