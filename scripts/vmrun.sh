#!/bin/bash
# 在 Parallels VM「MeeGo Build」里执行一个脚本。
# 用法：scripts/vmrun.sh <本地脚本路径> [参数...]
# prlctl exec 会二次分词，所以必须把脚本放到共享目录再按路径执行。
set -u
MAC_SHARE="/Users/zerox/WorkSpace/saidroid-next"
VM_SHARE="/media/psf/Home/WorkSpace/saidroid-next"
PRL="/Applications/Parallels Desktop.app/Contents/MacOS/prlctl"

local_script="$1"; shift || true
rel="${local_script#$MAC_SHARE/}"
vm_script="$VM_SHARE/$rel"
args="$*"

"$PRL" exec "MeeGo Build" "/bin/bash $vm_script $args" 2>&1
