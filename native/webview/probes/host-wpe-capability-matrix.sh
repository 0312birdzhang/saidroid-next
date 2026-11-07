#!/bin/sh
# Dump which WebKit WPE API entry points the installed libWPEWebKit actually
# exports, so docs/SD-WEBVIEW-DESIGN.md's contract-mapping table is grounded in
# the shipped ABI instead of upstream documentation.
# Read-only. Run on the device (or against the sysroot copy).
L=${1:-/usr/lib64/libWPEWebKit-2.0.so.1.11.4}
[ -r "$L" ] || { echo "cannot read $L"; exit 1; }
nm -D --defined-only "$L" | awk '{print $3}' | sort -u > /tmp/wpe-syms.txt
for sym in \
  webkit_web_view_load_uri webkit_web_view_load_html webkit_web_view_load_bytes \
  webkit_web_view_load_request webkit_web_view_load_plain_text \
  webkit_web_view_reload webkit_web_view_reload_bypass_cache webkit_web_view_stop_loading \
  webkit_web_view_can_go_back webkit_web_view_go_back webkit_web_view_can_go_forward webkit_web_view_go_forward \
  webkit_web_view_can_go_to_back_forward_list_item webkit_web_view_go_to_back_forward_list_item \
  webkit_web_view_get_uri webkit_web_view_get_title webkit_web_view_get_estimated_load_progress \
  webkit_web_view_get_zoom_level webkit_web_view_set_zoom_level \
  webkit_web_view_evaluate_javascript webkit_web_view_get_snapshot \
  webkit_web_view_get_network_session webkit_web_view_get_settings \
  webkit_web_view_set_settings webkit_web_view_get_user_content_manager \
  webkit_web_view_set_background_color \
  webkit_web_view_set_input_method_context webkit_web_view_get_input_method_context \
  webkit_web_view_get_page webkit_web_view_get_favicon \
  webkit_web_context_allow_tls_certificate_for_host webkit_web_context_register_uri_scheme \
  webkit_web_context_set_web_extensions_directory \
  webkit_user_content_manager_add_script webkit_user_content_manager_register_script_message_handler \
  webkit_user_script_new webkit_user_content_manager_remove_all_scripts \
  webkit_network_session_new webkit_network_session_get_cookie_manager \
  webkit_cookie_manager_get_cookies webkit_cookie_manager_get_all_cookies \
  webkit_cookie_manager_add_cookie webkit_cookie_manager_delete_cookie \
  webkit_cookie_manager_replace_cookies webkit_cookie_manager_set_persistent_storage \
  webkit_find_controller_new webkit_find_controller_search webkit_find_controller_search_next \
  webkit_find_controller_search_finish webkit_find_controller_count_matches \
  webkit_authentication_request_authenticate webkit_authentication_request_cancel \
  webkit_settings_set_javascript_can_access_clipboard webkit_settings_set_enable_webrtc \
  webkit_settings_set_enable_media_stream webkit_settings_set_enable_media \
  webkit_settings_set_enable_html5_local_storage webkit_settings_set_enable_html5_database \
  webkit_settings_set_enable_offline_web_application_cache \
  webkit_settings_set_enable_page_cache webkit_settings_set_enable_smooth_scrolling \
  webkit_settings_set_hardware_acceleration_policy webkit_settings_set_enable_2d_canvas_acceleration \
  webkit_settings_set_enable_webgl webkit_settings_set_enable_hyperlink_auditing \
  webkit_settings_set_enable_mediasource webkit_settings_set_enable_encrypted_media \
  webkit_print_operation_new webkit_print_operation_run_dialog \
  webkit_web_view_get_editor_state \
  ; do
    if grep -qx "$sym" /tmp/wpe-syms.txt; then echo "YES $sym"; else echo "NO  $sym"; fi
done
rm -f /tmp/wpe-syms.txt
