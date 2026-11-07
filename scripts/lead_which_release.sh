#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "=== device release files (md5) ==="
$SSH 'md5sum /home/art/releases/api29-npe36/lib/runtime.jar /home/art/releases/api29-npe36/java/dex/art/framework29-classes3.jar /home/art/releases/api29-npe36/lib/libsdwindow.so'
echo "=== candidate components on VM (md5) ==="
for r in r76 r77 r78; do
  d=/var/tmp/saidroid-next-api29-component-$r
  [ -d "$d" ] || continue
  echo "-- $r"
  find "$d" -name 'runtime.jar' -o -name 'framework29-classes3.jar' -o -name 'libsdwindow.so' 2>/dev/null | while read f; do
    md5sum "$f"
  done
done
