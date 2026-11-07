#!/bin/bash
# VM-side incremental native ART build, preserving the previous source and ELF.
set -euo pipefail
task_root="$(cd "$(dirname "$0")/.." && pwd)"
task_source=/tmp/art-build/art-standalone
task_output=/var/tmp/saidroid-next-jit-policy-20261025-r1
test ! -e "$task_output"
test "$(sha256sum "$task_source/art/runtime/oat_file_assistant.cc" | cut -d ' ' -f1)" = 1f29af27cf552281121173859868ce790ed6f3d399e43d8bf38346cf20c1adf7
mkdir -m0700 "$task_output"
cp "$task_source/art/runtime/oat_file_assistant.cc" "$task_output/oat_file_assistant.before.cc"
cp "$task_source/out/host/linux-x86/lib64/libart.so" "$task_output/libart.before.so"
cp "$task_source/out/host/linux-x86/lib64/libart-compiler.so" "$task_output/libart-compiler.before.so"
cp "$task_root/third_party/art-standalone/art/runtime/oat_file_assistant.cc" \
    "$task_source/art/runtime/oat_file_assistant.cc"
sha256sum "$task_source/art/runtime/oat_file_assistant.cc" > "$task_output/source.sha256"
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH="$JAVA_HOME/bin:$PATH"
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
bash "$task_root/scripts/complete-jit-runtime-build.sh"
printf 'jit_loading_policy_build=ready|output=%s\n' "$task_output"
