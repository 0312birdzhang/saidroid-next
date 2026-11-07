#!/bin/bash
SRC=/media/psf/Home/WorkSpace/saidroid-next
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no"
$SCP "$SRC/test/qq.apk" root@bonito:/tmp/ 2>&1|tail -1
$SCP "$SRC/runtime/macapk-loader.jar" "$SRC/runtime/android-framework.jar" root@bonito:/tmp/ 2>&1|tail -1
$SCP -r /tmp/jdkfull/jdk-21.0.13+9 root@bonito:/tmp/jdk 2>&1|tail -1
$SCP "$SRC/java/src/org/saidroid/AxmlReader.java" "$SRC/java/src/org/saidroid/ApkLoader.java" root@bonito:/tmp/ 2>&1|tail -1
$SSH 'cd /tmp
mkdir -p org/saidroid
cp AxmlReader.java ApkLoader.java org/saidroid/ 2>/dev/null
/tmp/jdk/bin/javac -cp "macapk-loader.jar:android-framework.jar" -d . org/saidroid/AxmlReader.java org/saidroid/ApkLoader.java 2>&1|head -5
echo "=== 解析 QQ Manifest ==="
/tmp/jdk/bin/java -Xmx2g -cp "/tmp:macapk-loader.jar:android-framework.jar" org.saidroid.ApkLoader qq.apk 2>&1 | head -8'
