#!/bin/sh
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
echo "== lock =="; /bin/sh /media/psf/Home/WorkSpace/saidroid-next/scripts/devlock.sh status | head -2
echo "== owned procs =="; $SSH "pgrep -af 'dalvikvm|saildroid-open|org.saildroid.manager' | head -5; echo END"
echo "== root =="; $SSH 'readlink /home/art/api29-root'
echo "== delete my release =="
$SSH 'if [ -d /home/art/releases/api29-whiteboard1 ]; then du -sh /home/art/releases/api29-whiteboard1; rm -rf /home/art/releases/api29-whiteboard1; echo DELETED; else echo NOT_PRESENT; fi'
echo "== releases now =="; $SSH 'ls -1 /home/art/releases; echo COUNT=$(ls -1 /home/art/releases | wc -l)'
echo "== root after =="; $SSH 'readlink /home/art/api29-root'
echo "== stale deploy stage =="; $SSH 'ls -d /home/art/test/api29-deploy-whiteboard* 2>/dev/null; du -sh /home/art/test/api29-deploy-whiteboard1 2>/dev/null; echo END'
