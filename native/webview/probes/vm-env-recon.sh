export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@192.168.2.15 '
echo "== strace/gdb"; which strace gdb ltrace 2>/dev/null; ls -l /usr/bin/strace 2>/dev/null
echo "== wayland displays"; ls -l /run/user/100000/display/ 2>/dev/null; ls -l /run/user/100000/ 2>/dev/null | head
echo "== who runs the browser"; pgrep -a -f atlantic | head -5
echo "== helper binary type"; file /usr/libexec/wpe-webkit-2.0/WPEWebProcess 2>/dev/null; ls -l /usr/libexec/wpe-webkit-2.0/
echo "== helper strings (env/exec)"; strings -a /usr/libexec/wpe-webkit-2.0/WPEWebProcess | grep -E "exec|/opt|/usr|WEBKIT|ATLANTIC|wpe-webkit" | head -25
echo "== userns"; cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null; ls -l /usr/bin/bwrap 2>/dev/null
'
