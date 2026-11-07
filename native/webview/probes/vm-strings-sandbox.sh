export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@192.168.2.15 '
L=/usr/lib64/libWPEWebKit-2.0.so.1.11.4
echo "== sandbox-related strings"
strings -a $L | grep -iE "^(WEBKIT_[A-Z_]*SANDBOX[A-Z_]*|WEBKIT_DISABLE_SANDBOX.*|WPE_[A-Z_]*)$" | sort -u
echo "== env vars referenced"
strings -a $L | grep -E "^WEBKIT_[A-Z0-9_]+$" | sort -u | head -40
echo "== process launch / helper hints"
strings -a $L | grep -E "bwrap|bubblewrap|userns|seccomp|WebProcessLauncher|ProcessLauncher" | sort -u | head -20
echo "== cgroup/helper paths"
strings -a $L | grep -E "^/usr/(bin|libexec|lib64)/.*(bwrap|sandbox|WebProcess)" | sort -u | head -20
'
