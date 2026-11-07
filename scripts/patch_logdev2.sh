#!/bin/bash
cd /tmp/art-build/art-standalone
python3 - <<'PY'
p="/tmp/art-build/art-standalone/system/core/liblog/fake_log_device.c"
src=open(p).read()
# 加 stdbool.h
if '#include <stdbool.h>' not in src:
    src = src.replace('#include <stdio.h>', '#include <stdio.h>\n#include <stdbool.h>', 1)
# 修重复定义
src = src.replace('''static bool should_colorize() {
    static bool should_colorize;
    static bool cached = false;''',
'''static bool should_colorize(void) {
    static bool s_should_colorize = false;
    static bool cached = false;''')
src = src.replace('return should_colorize;', 'return s_should_colorize;')
src = src.replace('should_colorize = true;', 's_should_colorize = true;')
src = src.replace('should_colorize = false;', 's_should_colorize = false;')
open(p,"w").write(src)
print("已修 bool")
PY
echo "=== 验证 ==="
sed -n '350,360p' system/core/liblog/fake_log_device.c 2>/dev/null
echo "=== 重新编译 ==="
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
timeout 240 make -j4 2>&1 | grep -E "error:|Error [0-9]|\*\*\*" | head -10
echo "=== 检查是否有产物 ==="
ls -la out/host/linux-x86/bin/ 2>/dev/null | head -5
