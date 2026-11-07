A=/tmp/art-build/bionic_translation/linker/linker.c
echo "=== apkenv_open_library 实现 ==="
grep -n -A40 "^apkenv_open_library\|static int$\|apkenv_open_library(const" $A | sed -n '/apkenv_open_library/,/^[0-9]*-}/p' | head -50
