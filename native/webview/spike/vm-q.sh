export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@192.168.2.15 '
echo "== soup cookie symbols"; nm -D --defined-only /usr/lib64/libsoup-3.0.so.0 | grep -E " soup_cookie_(new|get_name|get_value|get_domain|get_path|get_expires|get_secure|get_http_only|is_session|free|ref|unref|copy|set_)" | head -30
echo "== webkit cookie API"; nm -D --defined-only /usr/lib64/libWPEWebKit-2.0.so.1.11.4 | grep -E "webkit_cookie_manager_(get|add|delete|set|replace)_" | head -20
' 2>&1
