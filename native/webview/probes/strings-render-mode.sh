#!/bin/sh
# Read-only: which render-mode / compositing knobs does this WPE build understand?
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15"
WK=/usr/lib64/libWPEWebKit-2.0.so.1.11.4
echo "== env-style knobs mentioning composit/render/accelerat"
$SSH "strings -a $WK | grep -E '^(WEBKIT|WPE|JSC)_[A-Z0-9_]+$' | grep -i -E 'COMPOSIT|RENDER|ACCEL|GL|TEXTURE|TILE|BACKING' | sort -u"
echo
echo "== ThreadedCompositor / renderer backend selection strings"
$SSH "strings -a $WK | grep -E 'ThreadedCompositor|TextureMapper|AcceleratedCompositing|ForceCompositingMode|disables? .*compositing' | sort -u | head -30"
echo
echo "== does the WebProcess have a CPU-only compositing path string?"
$SSH "strings -a $WK | grep -E 'CPU.*[Cc]omposit|Software.*[Cc]omposit|skia.*cpu|Skia.*CPU' | sort -u | head -20"
echo
echo "== WPEView / fdo target creation call sites"
$SSH "strings -a $WK | grep -E 'wpe_renderer_backend_egl_target|wpe_view_backend_exportable_fdo|wpe_fdo_initialize' | sort -u"
