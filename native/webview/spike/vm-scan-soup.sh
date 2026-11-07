#!/bin/sh
# Enumerate Soup types referenced by the device WPE headers (to build a compile-only stub).
set -u
D=/var/tmp/sd-webview-spike/include/wpe-webkit-2.0
echo "== headers including libsoup"
grep -l "libsoup/soup.h" "$D"/wpe/*.h "$D"/jsc/*.h 2>/dev/null
echo "== Soup* identifiers used"
grep -ohE "Soup[A-Za-z0-9_]+" "$D"/wpe/*.h 2>/dev/null | sort -u
echo "== jsc headers present"
ls "$D"/jsc | head
echo DONE
