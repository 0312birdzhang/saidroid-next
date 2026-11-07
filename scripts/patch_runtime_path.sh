#!/bin/bash
cd /tmp/art-build/art-standalone
cp art/runtime/runtime.cc art/runtime/runtime.cc.bak 2>/dev/null
echo "=== 修复 GetCompilerExecutable 的路径拼接 ==="
python3 - <<'PY'
p="/tmp/art-build/art-standalone/art/runtime/runtime.cc"
src=open(p).read()
old = '''    std::string compiler_executable(GetAndroidRoot());
    compiler_executable += dex2oat_name;'''
new = '''    std::string compiler_executable(GetAndroidRoot());
    if (compiler_executable.back() != '/') {
      compiler_executable += '/';
    }
    compiler_executable += "bin/";
    compiler_executable += dex2oat_name;'''
if old in src:
    src = src.replace(old, new)
    open(p,"w").write(src)
    print("已修复：加了 /bin/ 分隔")
else:
    print("未找到目标代码")
PY
echo "=== 验证 ==="
sed -n '800,815p' art/runtime/runtime.cc 2>/dev/null
