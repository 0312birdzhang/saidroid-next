#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== runtime.cc 795-815 ==="
sed -n '790,820p' art/runtime/runtime.cc 2>/dev/null
