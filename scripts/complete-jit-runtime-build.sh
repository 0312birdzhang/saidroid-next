#!/bin/bash
# Complete only the native runtime targets, not unrelated platform executables.
set -euo pipefail
task_root="$(cd "$(dirname "$0")/.." && pwd)"
task_source=/tmp/art-build/art-standalone
task_output=/var/tmp/saidroid-next-jit-policy-20261025-r1
test -f "$task_output/source.sha256"
test ! -e "$task_output/runtime-targets.log"
sha256sum -c "$task_output/source.sha256"
cmp "$task_root/third_party/art-standalone/art/runtime/oat_file_assistant.cc" \
    "$task_source/art/runtime/oat_file_assistant.cc"
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH="$JAVA_HOME/bin:$PATH"
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
export LD_LIBRARY_PATH=/usr/local/lib
cd "$task_source"
make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a ART_HOST_CODEGEN_ARCHS=arm64 \
    out/host/linux-x86/lib64/libart.so out/host/linux-x86/lib64/libart-compiler.so \
    > "$task_output/runtime-targets.log" 2>&1
gcc -shared -fPIC -O2 -I/usr/local/include -L/usr/local/lib -Wl,-rpath,/usr/local/lib \
    -o "$task_output/libsaidroid-unwind-compat.so" "$task_root/native/unwind-compat.c" -lunwind-aarch64
sha256sum out/host/linux-x86/lib64/libart.so out/host/linux-x86/lib64/libart-compiler.so \
    > "$task_output/binaries.sha256"
printf 'jit_loading_runtime_targets=ready|output=%s\n' "$task_output"
