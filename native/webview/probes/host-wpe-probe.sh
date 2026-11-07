#!/bin/sh
# Probe WPE WebKit / Qt platform plugins / user session on the host.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"

echo "===== WPE packages"
$SSH 'rpm -qa | grep -i -E "^wpe|libwpe|cog" | sort; rpm -q --whatprovides /usr/lib64/libWPEWebKit-2.0.so.1 2>&1'

echo "===== WPE libs"
$SSH 'ls -la /usr/lib64/libWPE* /usr/lib64/libwpe* 2>&1'

echo "===== WPE backends"
$SSH 'ls -la /usr/lib64/libwpebackend* /usr/lib64/wpe* 2>&1; ls -la /usr/lib64/wpe-1.0 2>&1; ls -la /usr/lib64/wpe-2.0 2>&1'

echo "===== WPE headers"
$SSH 'ls -d /usr/include/wpe* /usr/include/WPE* /usr/include/wpe-1.0 2>&1'

echo "===== atlantic-browser (WPE-based?)"
$SSH 'ldd /usr/bin/atlantic-browser.bin 2>&1 | head -40; echo ---ENV---; cat /usr/bin/atlantic-browser-env 2>&1; echo ---WRAP---; cat /usr/bin/atlantic-browser 2>&1'

echo "===== WPE introspection"
$SSH 'ls /usr/lib64/girepository-1.0/ 2>&1 | head -20'

echo "===== qt platforms"
$SSH 'ls -la /usr/lib64/qt5/plugins/platforms/ 2>&1; ls -la /usr/lib64/qt5/plugins/scenegraph/ 2>&1'

echo "===== user runtime dir"
$SSH 'ls -la /run/user/ 2>&1; id defaultuser 2>&1; ls -la /run/user/100000/ 2>&1 | head -30'

echo "===== wayland socket real"
$SSH 'find /run -maxdepth 3 -name "wayland-*" 2>/dev/null; ls -la /run/wayland* 2>&1 | head'

echo "===== lipstick env of compositor"
$SSH 'P=$(pgrep -f lipstick | head -1); echo LIP=$P; tr "\0" "\n" < /proc/$P/environ 2>/dev/null | grep -E "WAYLAND|XDG|QT_|EGL|LIBGL|HYBRIS|MESA" | sort'

echo "===== browser process env for engine"
$SSH 'P=$(pgrep -f "booster-browser" | tail -1); echo BR=$P; tr "\0" "\n" < /proc/$P/environ 2>/dev/null | grep -E "MOZ|EMBED|QT_|WAYLAND|XDG" | sort | head -40'

echo "===== OpenGL libs"
$SSH 'ls -la /usr/lib64/libEGL.so* /usr/lib64/libGLESv2.so* /usr/lib64/libgbm* /usr/lib64/libwayland-client* 2>&1'

echo "===== host CPU"
$SSH 'grep -c ^processor /proc/cpuinfo; head -2 /proc/cpuinfo'

echo "DONE"
