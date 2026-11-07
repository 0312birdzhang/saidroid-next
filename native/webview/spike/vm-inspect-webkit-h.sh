#!/bin/sh
D=/var/tmp/sd-webview-spike/include/wpe-webkit-2.0/wpe
echo "== webkit.h"
sed -n 1,80p "$D/webkit.h"
echo "== size"
wc -l "$D/webkit.h"
echo DONE
