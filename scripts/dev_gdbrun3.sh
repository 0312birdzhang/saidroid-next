#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
cat > /tmp/dev_gdb3.cmds <<'CMDS'
set pagination off
set confirm off
set breakpoint pending on
handle SIG34 nostop noprint pass
handle SIG35 nostop noprint pass
handle SIG36 nostop noprint pass
handle SIG37 nostop noprint pass
handle SIGSEGV nostop noprint pass
break abort
run
printf "\n=== AT ABORT ===\n"
bt 30
printf "\n=== END ===\n"
kill
quit
CMDS
sshpass -e scp -o StrictHostKeyChecking=no /tmp/dev_gdb3.cmds root@bonito:/home/art/test/dev_gdb3.cmds
$SSH '. /home/art/env.sh; cd /home/art/test
      gdb -batch -nx -x /home/art/test/dev_gdb3.cmds --args \
        /home/art/bin/dalvikvm -cp /home/art/test/ap.dex QQProbe \
          /home/art/bio2 /home/art/lib/libsdbridge.so /home/art/realapps/qq.apk /home/art/realapps/qq-libs \
        > /home/art/test/gdb3.log 2>&1
      echo gdb-rc=$?'
echo "=== ABORT 段 ==="
$SSH "grep -av 'packed reloc' /home/art/test/gdb3.log | sed -n '/=== AT ABORT ===/,/=== END ===/p' | head -32"
