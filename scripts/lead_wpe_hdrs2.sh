#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "for f in renderer-host.h renderer-backend-egl.h wpe-egl.h view-backend.h; do echo \"===== \$f =====\"; sed -n '30,120p' /usr/include/wpe-1.0/wpe/\$f; done"
