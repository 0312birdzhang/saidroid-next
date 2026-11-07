#!/bin/sh
echo "== wpe/loader.h =="
sed -n '1,80p' /usr/include/wpe-1.0/wpe/loader.h 2>/dev/null || echo NO_HEADER
