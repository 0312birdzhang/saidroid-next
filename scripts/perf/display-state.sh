#!/bin/bash
# Read-only device state that can explain sparse compositor frame callbacks:
# is the screen on / dimmed, is a screensaver up, is our window marked visible.
# Runs on the phone; prints KEY=VALUE lines.
echo "TIME=$(date -Is)"
if command -v gdbus >/dev/null 2>&1; then
  echo "MCE_DISPLAY_STATUS=$(gdbus call --system --dest com.nokia.mce \
      --object-path /com/nokia/mce/request \
      --method com.nokia.mce.request.get_display_status 2>&1 | tr '\n' ' ')"
else
  echo "MCE_DISPLAY_STATUS=no-gdbus"
fi
for f in /sys/class/backlight/*/brightness /sys/class/backlight/*/max_brightness; do
  [ -e "$f" ] && echo "BACKLIGHT_$(basename "$(dirname "$f")")_$(basename "$f")=$(cat "$f" 2>/dev/null)"
done
[ -e /sys/class/graphics/fb0/blank ] && echo "FB_BLANK=$(cat /sys/class/graphics/fb0/blank)"
for d in /sys/class/drm/card0-*/status; do
  [ -e "$d" ] && echo "DRM_$(basename "$(dirname "$d")")_status=$(cat "$d")"
done
echo "LIPSTICK_PROC=$(pgrep -fa lipstick | head -3 | tr '\n' ';')"
echo "LIPSTICK_CPU=$(ps -o pid,pcpu,etime,comm -C lipstick --no-headers 2>/dev/null | tr '\n' ';')"
