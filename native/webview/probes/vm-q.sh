export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@192.168.2.15 '
L=/usr/lib64/libWPEWebKit-2.0.so.1.11.4
nm -D --defined-only $L | awk "{print \$3}" | sort -u > /tmp/s.txt
for s in webkit_web_view_get_find_controller webkit_web_view_is_loading webkit_web_view_get_back_forward_list webkit_back_forward_list_get_nth_item webkit_back_forward_list_get_back_list_with_limit webkit_web_view_get_session_state webkit_web_view_restore_session_state webkit_input_method_context_new webkit_input_method_context_get_type webkit_settings_set_enable_media_stream webkit_web_view_get_main_resource webkit_web_view_get_custom_charset webkit_web_view_set_custom_charset webkit_web_view_set_zoom_level webkit_web_context_new webkit_web_context_get_default webkit_web_view_new_with_settings webkit_web_view_new_with_user_content_manager webkit_web_view_new_with_related_view webkit_web_view_new_with_context; do
  grep -qx $s /tmp/s.txt && echo "YES $s" || echo "NO  $s"
done
echo "== signals (strings guess)"
strings -a $L | grep -E "^(script-dialog|authenticate|run-file-chooser|download-started|load-failed-with-tls-errors|web-process-terminated|web-process-crashed|permission-request|context-menu|show-notification|mouse-target-changed|ready-to-show)$" | sort -u
rm -f /tmp/s.txt
'
