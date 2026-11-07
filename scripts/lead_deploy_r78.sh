#!/bin/bash
# 把已构建好的 component-r78 正式装成 releases/api29-r78 并切 root。
set -eu
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
cd /media/psf/Home/WorkSpace/saidroid-next
echo "=== step1 close all owned ==="
/bin/bash scripts/lead_close_all.sh
echo "=== step2 clear stale staging ==="
sshpass -e ssh -o StrictHostKeyChecking=no root@bonito 'rm -rf /home/art/test/api29-deploy-r78; echo CLEARED'
echo "=== step3 deploy ==="
python3 scripts/api29/deploy-component.py /var/tmp/saidroid-next-api29-component-r78 r78 2>&1 | tail -12
echo "=== step4 verify ==="
sshpass -e ssh -o StrictHostKeyChecking=no root@bonito 'readlink /home/art/api29-root; md5sum /home/art/releases/api29-r78/lib/runtime.jar /home/art/releases/api29-r78/java/dex/art/framework29-classes3.jar; df -h / | tail -1'
echo "=== step5 release lock ==="
cd /media/psf/Home/WorkSpace/saidroid-next && /bin/bash scripts/devlock.sh release lead-npe || true
