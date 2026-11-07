#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH 'cd /tmp
echo "=== SplashActivity 的继承链 ==="
/tmp/jdk/bin/javap -p /tmp/splash.class 2>/dev/null | head -5
echo "=== 是否 extends Activity ==="
/tmp/jdk/bin/javap -p /tmp/splash.class 2>/dev/null | grep "class SplashActivity"
echo "=== 关键方法 ==="
/tmp/jdk/bin/javap -p /tmp/splash.class 2>/dev/null | grep -E "onCreate|onResume|onStart" | head -5'
