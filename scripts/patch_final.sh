#!/bin/bash
F=/tmp/art-build/art-standalone/system/core/liblog/fake_log_device.c
echo "=== 修复前 ==="
sed -n '352,356p' $F
python3 - <<'PY'
p="/tmp/art-build/art-standalone/system/core/liblog/fake_log_device.c"
src=open(p).read()

# 1. 加 stdbool.h（如果缺）
if '<stdbool.h>' not in src:
    src = src.replace('#include <string.h>', '#include <string.h>\n#include <stdbool.h>', 1)

# 2. 整体替换 should_colorize 函数
import re
pat = re.compile(r'static bool should_colorize\(\)\s*\{.*?\n\}', re.S)
m = pat.search(src)
if m:
    newfunc = '''static bool should_colorize(void) {
    static bool s_colorize = false;
    static bool cached = false;
    if (cached)
        return s_colorize;

    {
        char *liblog_color = getenv("LIBLOG_COLOR");
        if (liblog_color) {
            if (!strcmp(liblog_color, "always")) {
                s_colorize = true;
            } else if (!strcmp(liblog_color, "never")) {
                s_colorize = false;
            } else {
                fprintf(stderr, "liblog: invalid LIBLOG_COLOR value\\n");
                exit(1);
            }
        } else {
            s_colorize = isatty(fileno(stderr)) ? true : false;
        }
    }
    cached = true;
    return s_colorize;
}'''
    src = src[:m.start()] + newfunc + src[m.end():]
    open(p,"w").write(src)
    print("OK: 已替换整个函数")
else:
    print("FAIL: 未匹配到函数")
PY
echo "=== 修复后 ==="
sed -n '352,380p' $F | head -28
