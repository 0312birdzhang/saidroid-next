#!/bin/bash
SRC=/media/psf/Home/WorkSpace/saidroid-next
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no"
$SCP "$SRC/scripts/QB.java" root@bonito:/tmp/ 2>/dev/null || echo "QB.java 不存在"
$SSH 'cd /tmp
ls -la QB.java 2>/dev/null
echo "=== 清理并分批转换（每批 3 个，限内存 1.8G）==="
rm -rf out && mkdir -p out
/tmp/jdk/bin/java -Xmx1800m -cp "/tmp:macapk-loader.jar" QB 3 2>&1 | grep -E "QB=|OutOfMemory" | head -20'
