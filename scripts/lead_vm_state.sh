#!/bin/bash
set -u
echo "=== /var/tmp saidroid dirs ==="
ls -dlt /var/tmp/saidroid-next-api29-* 2>/dev/null | head -12
echo "=== product r118 ==="
ls -l /var/tmp/saidroid-next-api29-product-20261026-r118/ 2>/dev/null | head -10
echo "=== inputs candidates ==="
for d in /var/tmp/saidroid-next-api29-inputs-*; do [ -d "$d" ] && echo "$d" && ls "$d" | head -5; done 2>/dev/null | head -20
echo "=== java home ==="
ls -d /tmp/jdkfull/jdk-21* 2>/dev/null; which javac gcc g++ wayland-scanner 2>/dev/null
