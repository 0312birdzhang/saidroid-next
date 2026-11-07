export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@192.168.2.15 '
L=/usr/lib64/libWPEWebKit-2.0.so.1.11.4
echo "== WEBKIT_/WPE_ env vars"
strings -a $L | grep -E "^WEBKIT_[A-Z0-9_]+$" | sort -u | head -40
echo "== bwrap/userns/seccomp"
strings -a $L | grep -E "bwrap|bubblewrap|unprivileged_userns|seccomp|ProcessLauncher|Sandbox" | sort -u | head -25
echo "== wpe_sfos_* defined symbols"
nm -D --defined-only $L | awk "{print \$3}" | grep -E "^wpe_sfos_|renderer_host|preconnect" | sort -u
echo "== /opt/wpe-sfos tree (depth 3)"
find /opt/wpe-sfos -maxdepth 3 | head -40
echo "== atlantic runtime-common.sh key lines"
grep -nE "preconnect|WAYLAND|renderer|WPE_|sandbox|GRALLOC|HYBRIS" /opt/wpe-sfos/libexec/atlantic/runtime-common.sh 2>/dev/null | head -40
'
