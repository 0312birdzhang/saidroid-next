set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$SCP /tmp/vk/inject_volkeys root@bonito:/home/art/inject_volkeys
echo "=== 截图目录（注入前）==="
$SSH "ls -lt /home/defaultuser/Pictures/Screenshots/ 2>/dev/null | head -3; echo '---'; ls -lt /home/defaultuser/Pictures/ 2>/dev/null | head -5"
echo "=== 注入音量键组合 ==="
$SSH "chmod +x /home/art/inject_volkeys; /home/art/inject_volkeys 150; sleep 3"
echo "=== 截图目录（注入后）==="
$SSH "ls -lt /home/defaultuser/Pictures/Screenshots/ 2>/dev/null | head -4; echo '---'; find /home/defaultuser -newermt '-2 minutes' -name '*.png' 2>/dev/null | head -5"
