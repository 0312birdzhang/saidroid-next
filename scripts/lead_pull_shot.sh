#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
n=${1:-pm-check}
sshpass -e scp -o StrictHostKeyChecking=no \
  root@bonito:/home/defaultuser/Downloads/SailDroid-Screenshots/$n.png \
  /media/psf/Home/WorkSpace/saidroid-next/build/screens/$n.png && \
  ls -l /media/psf/Home/WorkSpace/saidroid-next/build/screens/$n.png
