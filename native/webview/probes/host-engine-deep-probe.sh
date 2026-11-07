#!/bin/sh
# Deeper read-only probe: identify the host's real browser engine (Gecko/embedlite?).
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"

echo "===== mozilla-ish packages"
$SSH 'rpm -qa | grep -i -E "mozilla|xulrunner|mozjs|qmoz|embedlite|nspr|nss" | sort'

echo "===== libxul/mozjs"
$SSH 'ls -la /usr/lib64/libxul.so* /usr/lib64/libmozjs* /usr/lib64/libnspr4.so* /usr/lib64/libnss3.so* /usr/lib64/libnssutil3.so* /usr/lib64/libsmime3.so* /usr/lib64/libssl3.so* 2>&1'

echo "===== qmozembed"
$SSH 'ls -la /usr/lib64/libqmozembed* /usr/lib64/*embedlite* 2>&1; ls /usr/lib64/qt5/qml/Qt5Mozilla/ 2>&1; ls /usr/lib64/qt5/qml/Qt5MozillaNext153/ 2>&1'

echo "===== sailfish-browser pkg deps/files"
$SSH 'rpm -q --whatprovides libxul.so 2>&1; rpm -q --whatrequires libxul.so 2>&1 | head; rpm -qi sailfish-browser 2>&1 | head -20'

echo "===== embedlite components"
$SSH 'rpm -qa | grep -i -E "embedlite|browser" | sort'

echo "===== gecko executable"
$SSH 'ls -la /usr/lib64/xulrunner* /usr/bin/*browser* /usr/libexec/*browser* 2>&1 | head -20'

echo "===== sailfish-browser binary+ldd"
$SSH 'file /usr/bin/sailfish-browser 2>&1; ldd /usr/bin/sailfish-browser 2>&1 | head -40'

echo "===== browser booster ldd"
$SSH 'ldd /usr/libexec/mapplauncherd/booster-browser 2>&1 | head -30'

echo "===== process maps for live gecko"
$SSH 'P=$(pgrep -f booster-browser | head -1); echo PID=$P; [ -n "$P" ] && grep -E "libxul|libmozjs|libqmoz|embedlite" /proc/$P/maps | head -20'

echo "===== QtWebKit/WebEngine again, whole fs"
$SSH 'find /usr/lib64 /usr/libexec -maxdepth 2 -name "*WebEngine*" -o -maxdepth 2 -name "*WebKit*" 2>/dev/null | head -20'

echo "===== chromium/cef"
$SSH 'rpm -qa | grep -i -E "chromium|cef|electron" | sort; ls /usr/lib64/libcef* 2>&1'

echo "===== python gtk webkit?"
$SSH 'rpm -qa | grep -i -E "webkit|gtk3|wpe" | sort | head -20'

echo "===== webview permission profile"
$SSH 'cat /etc/sailjail/permissions/WebView.permission 2>&1'

echo "===== xulrunner version"
$SSH 'ls /usr/lib64/xulrunner-qt5* 2>/dev/null; cat /usr/lib64/xulrunner*/application.ini 2>/dev/null; rpm -qa | grep -i xul | sort'

echo "DONE"
