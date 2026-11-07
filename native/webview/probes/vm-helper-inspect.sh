export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e scp -o StrictHostKeyChecking=no /media/psf/Home/WorkSpace/saidroid-next/native/webview/probes/host-helper-inspect.sh root@192.168.2.15:/tmp/hi.sh >/dev/null 2>&1
sshpass -e ssh -o StrictHostKeyChecking=no root@192.168.2.15 'sh /tmp/hi.sh; rm -f /tmp/hi.sh'
