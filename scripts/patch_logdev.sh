#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 改代码：C99 声明式 if → C89 兼容写法 ==="
python3 - <<'PY'
p="/tmp/art-build/art-standalone/system/core/liblog/fake_log_device.c"
src=open(p).read()
old = '''    if (char *liblog_color = getenv("LIBLOG_COLOR")) {'''
new = '''    char *liblog_color = getenv("LIBLOG_COLOR");
    if (liblog_color) {'''
if old in src:
    src = src.replace(old, new)
    open(p,"w").write(src)
    print("已改为 C89 兼容")
else:
    print("未找到目标")
PY
echo "=== 同时把 bool 改成 int ==="
grep -n "bool should_colorize\|static bool" system/core/liblog/fake_log_device.c 2>/dev/null | head -3
