#!/bin/bash
SRC=/media/psf/Home/WorkSpace/saidroid-next
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no"
$SCP "$SRC/scripts/QB.java" root@bonito:/tmp/ 2>&1|tail -1
$SSH 'cd /tmp
/tmp/jdk/bin/javac -cp macapk-loader.jar -d . QB.java 2>&1|head -3
echo "=== 分批转换（每批 3 个）==="
rm -rf out && mkdir -p out
nohup /tmp/jdk/bin/java -Xmx1800m -cp "/tmp:macapk-loader.jar" QB 3 > /tmp/qb.log 2>&1 &
echo "PID=$!"
sleep 60
grep -E "QB=" /tmp/qb.log | tail -8
echo "=== 内存 ==="
free -m | head -2'
