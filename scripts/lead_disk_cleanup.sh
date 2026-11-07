#!/bin/bash
# 清掉 /home/art 下已作废的历史 release 与部署暂存目录，保留 r63 基线与 perf 对照。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
KEEP="api29-20261026-r63 api29-20261026-perf3 api29-20261026-perf6"
$SSH "set -e
  for d in /home/art/releases/api29-*; do
    n=\$(basename \$d)
    case ' $KEEP ' in *\" \$n \"*) continue;; esac
    rm -rf \$d
  done
  rm -rf /home/art/test/api29-deploy-*
  df -h /home/art | tail -1
  ls /home/art/releases | tr '\n' ' '
  echo"
