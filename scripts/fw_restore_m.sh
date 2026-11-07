#!/bin/bash
# 恢复 6.0.1 框架 jar 到 boot classpath
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
echo "=== 备份内容 ==="
ls -lh /tmp/fw-backup-m/ 2>/dev/null | head -6
for f in /tmp/fw-backup-m/framework*-hostdex.jar; do cp -f "$f" $BASE/java/dex/art/; done
rm -rf /.cache/art /tmp/art-data/.cache 2>/dev/null
ls -lh $BASE/java/dex/art/framework*hostdex.jar
echo "已恢复 6.0.1"
