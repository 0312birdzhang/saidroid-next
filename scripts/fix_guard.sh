#!/bin/bash
cd /tmp/art-build/art-standalone
python3 - <<'PY'
p="/tmp/art-build/art-standalone/art/runtime/runtime.cc"
src=open(p).read()
old = '''    std::string compiler_executable(GetAndroidRoot());
    if (compiler_executable.back() != '/') {
      compiler_executable += '/';
    }
    compiler_executable += "bin/";
    compiler_executable += dex2oat_name;
    return compiler_executable;'''
new = '''    std::string compiler_executable(GetAndroidRoot());
    if (compiler_executable.empty()) {
      return dex2oat_name;  // fall back to PATH
    }
    if (compiler_executable.back() != '/') {
      compiler_executable += '/';
    }
    compiler_executable += "bin/";
    compiler_executable += dex2oat_name;
    return compiler_executable;'''
if old in src:
    src = src.replace(old, new)
    open(p,"w").write(src)
    print("已加空字符串保护")
else:
    print("未找到")
PY
echo "=== 重编译 ==="
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
cd /tmp/art-build/art-standalone
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a ART_HOST_CODEGEN_ARCHS=arm64 > /tmp/art-rb2.log 2>&1 &
sleep 150
echo "错误: $(grep -c 'error:' /tmp/art-rb2.log 2>/dev/null || echo 0)"
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo DONE
