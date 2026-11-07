#!/bin/bash
cd /tmp/art-build/art-standalone
cp art/compiler/Android.mk art/compiler/Android.mk.bak 2>/dev/null
echo "=== 移除 arm64 对 arm(32位) 的依赖 ==="
python3 - <<'PY'
p="/tmp/art-build/art-standalone/art/compiler/Android.mk"
src=open(p).read()
# 找到 arm64 段里的 $(libart-compiler-defaults_arm_CODEGEN_SRCS)
old = '''        utils/arm64/managed_register_arm64.cc \\
        $(libart-compiler-defaults_arm_CODEGEN_SRCS)'''
new = '''        utils/arm64/managed_register_arm64.cc'''
if old in src:
    src = src.replace(old, new)
    open(p,"w").write(src)
    print("已移除 arm 依赖")
else:
    print("未找到，检查实际内容")
    import re
    m = re.search(r'libart-compiler-defaults_arm64_CODEGEN_SRCS.*?\n\n', src, re.S)
    if m: print(m.group()[:500])
PY
echo "=== 验证 ==="
sed -n '34,46p' art/compiler/Android.mk 2>/dev/null
