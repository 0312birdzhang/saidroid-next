#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== parsed_options.cc 585-600 ==="
sed -n '585,600p' art/runtime/parsed_options.cc 2>/dev/null
