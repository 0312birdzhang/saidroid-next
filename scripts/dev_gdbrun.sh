#!/bin/bash
# 在真机上用 gdb 抓 loadLibrary 里的 free() 崩溃
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
cat > /tmp/dev_gdb.cmds <<'CMDS'
set pagination off
set confirm off
set breakpoint pending on
handle SIGABRT stop print nopass
handle SIGSEGV stop print nopass
run
printf "\n=== FAULT ===\n"
bt 25
printf "\n=== MAPS ===\n"
info proc mappings
printf "\n=== END ===\n"
kill
quit
CMDS
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e scp -o StrictHostKeyChecking=no /tmp/dev_gdb.cmds root@bonito:/home/art/test/dev_gdb.cmds
$SSH '. /home/art/env.sh; cd /home/art/test
      gdb -batch -nx -x /home/art/test/dev_gdb.cmds --args \
        /home/art/bin/dalvikvm -cp /home/art/test/ap.dex QQProbe \
          /home/art/bio2 /home/art/lib/libsdbridge.so /home/art/realapps/qq.apk /home/art/realapps/qq-libs \
        > /home/art/test/gdb.log 2>&1
      echo gdb-rc=$?'
echo "=== FAULT 段 ==="
$SSH "grep -av 'packed reloc' /home/art/test/gdb.log | sed -n '/=== FAULT ===/,/=== MAPS ===/p' | head -30"
