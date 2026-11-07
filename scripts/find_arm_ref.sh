#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 谁 include assembler_arm_vixl.h ==="
grep -rn "assembler_arm_vixl.h" art/compiler/ 2>/dev/null | grep -v "\.o:" | head -5
echo
echo "=== 谁还在编 intrinsics_arm_vixl ==="
grep -rn "intrinsics_arm_vixl\|code_generator_arm_vixl" art/compiler/Android.mk 2>/dev/null | head -5
