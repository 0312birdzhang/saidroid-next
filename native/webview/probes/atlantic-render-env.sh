#!/bin/sh
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15"
F=/opt/wpe-sfos/libexec/atlantic/runtime-common.sh
echo "== SKIA / CPU raster / composition knobs in Atlantic's runtime"
$SSH "grep -n -i -E 'SKIA|CPU_RENDERING|USE_SKIA|RASTER|COMPOSIT|TILE_|GL_FINISH|EGL_PIXEL|FORCE' $F"
echo
echo "== full 'profile' definitions (lean/moderate/min/baseline?)"
$SSH "sed -n '230,340p' $F"
