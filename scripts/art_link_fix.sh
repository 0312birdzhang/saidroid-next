#!/bin/bash
echo "=== 装别名库 ==="
cp /tmp/uwp/alias.so /usr/local/lib/libunwind_alias.so 2>/dev/null
echo "=== 在 libdl_bio 里解析这个符号（直接重链接）==="
cd /tmp/art-build/bionic_translation
LDFLAGS="-L/usr/local/lib -lunwind_alias" ninja -C builddir -t clean libdl_bio.so.0.0.1 2>&1 | tail -2
LDFLAGS="-L/usr/local/lib -lunwind_alias" ninja -C builddir libdl_bio.so.0.0.1 2>&1 | tail -5
echo "=== 验证 ==="
nm -D builddir/libdl_bio.so.0.0.1 2>/dev/null | grep iterate | head -3
echo "=== 装 ==="
cp -a builddir/libdl_bio.so.0.0.1 /usr/local/lib/ 2>/dev/null
ldconfig 2>/dev/null
echo "=== 现在重链接 art ==="
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
export LD_LIBRARY_PATH=/usr/local/lib
cd /tmp/art-build/art-standalone
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a ART_HOST_CODEGEN_ARCHS=arm64 > /tmp/art-build15.log 2>&1 &
sleep 180
echo "错误: $(grep -c 'error:' /tmp/art-build15.log 2>/dev/null || echo 0)"
grep -E "cannot find|undefined reference" /tmp/art-build15.log 2>/dev/null | head -3
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
