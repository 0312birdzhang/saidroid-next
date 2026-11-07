#!/bin/bash
cd /tmp/art-build/art-standalone
python3 - <<'PY'
p="/tmp/art-build/art-standalone/system/core/liblog/fake_log_device.c"
src=open(p).read()

# 找到整个 should_colorize 函数并替换
import re
start = src.find('static bool should_colorize')
if start < 0:
    start = src.find('static bool s_s_should_colorize')
# 找函数结束（下一个顶层函数或 #ifdef）
end = src.find('\n}', start)
if end > 0:
    end += 2
    newfunc = '''static int should_colorize(void) {
    static int s_colorize = -1;
    if (s_colorize >= 0)
        return s_colorize;

    {
        char *liblog_color = getenv("LIBLOG_COLOR");
        if (liblog_color) {
            if (!strcmp(liblog_color, "always")) {
                s_colorize = 1;
            } else if (!strcmp(liblog_color, "never")) {
                s_colorize = 0;
            } else {
                fprintf(stderr, "liblog: invalid LIBLOG_COLOR value\\n");
                exit(1);
            }
        } else {
            s_colorize = isatty(fileno(stderr)) ? 1 : 0;
        }
    }
    return s_colorize;
}
'''
    src = src[:start] + newfunc + src[end:]
    open(p,"w").write(src)
    print("已重写 should_colorize 函数")
else:
    print("未找到函数边界")
PY
echo "=== 验证 ==="
sed -n '350,380p' system/core/liblog/fake_log_device.c 2>/dev/null | head -30
