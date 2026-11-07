#!/bin/bash
cd /tmp && rm -rf libunwind-src
echo "=== 克隆 libunwind ==="
git clone --depth 1 -q -b v1.8.1 https://github.com/libunwind/libunwind.git libunwind-src 2>&1 | head -3
cd libunwind-src 2>/dev/null || exit 1
echo "=== 构建 ==="
autoreconf -i 2>&1 | tail -2
./configure --prefix=/usr/local --enable-cxx-exceptions --disable-tests 2>&1 | tail -5
make -j4 2>&1 | tail -8
echo "=== 安装 ==="
make install 2>&1 | tail -5
ldconfig 2>/dev/null
echo "=== 验证 ==="
ls /usr/local/lib/libunwind* 2>/dev/null | head -5
nm -D /usr/local/lib/libunwind.so 2>/dev/null | grep -c "unw_set_iterate_phdr_function"
