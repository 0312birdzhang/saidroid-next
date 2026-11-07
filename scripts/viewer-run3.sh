#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15"
H=root@bonito
echo "=== 先停进程 ==="
$SSH $H 'pkill -f /home/art/sdview 2>/dev/null; sleep 1; pgrep -f sdview | head -2; echo killed'
echo "=== 再推送（校验 md5）==="
$SSH $H 'rm -f /home/art/sdview'
$SSH $H 'cat > /home/art/sdview' < /tmp/sdview/sdview
$SSH $H 'chmod +x /home/art/sdview; md5sum /home/art/sdview'
md5 -q /tmp/sdview/sdview
echo "=== 运行 ==="
$SSH $H 'rm -f /home/art/show.log; setsid /home/art/show.sh < /dev/null > /home/art/show.log 2>&1 & echo started'
sleep 20
$SSH $H 'echo "=== viewer 输出 ==="; head -20 /home/art/show.log 2>/dev/null'
