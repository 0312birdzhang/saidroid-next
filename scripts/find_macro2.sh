#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 全局搜 ART_ENABLE_CODEGEN ==="
grep -rn "ART_ENABLE_CODEGEN" build/ art/ 2>/dev/null | grep -v "\.o:" | head -15
