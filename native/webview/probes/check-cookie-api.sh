#!/bin/sh
# Read-only check of cookie API shape on device (for the spike's cookie test).
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
$SSH 'grep -n -E "get_cookies|add_cookie|WebKitCookie|SoupCookie" /usr/include/wpe-webkit-2.0/wpe/WebKitCookieManager.h | head -30'
$SSH 'grep -n -E "get_cookie_manager|webkit_network_session" /usr/include/wpe-webkit-2.0/wpe/WebKitNetworkSession.h | head -20'
$SSH 'grep -n -A6 "webkit_web_view_evaluate_javascript" /usr/include/wpe-webkit-2.0/wpe/WebKitWebView.h | head -40'
echo DONE
