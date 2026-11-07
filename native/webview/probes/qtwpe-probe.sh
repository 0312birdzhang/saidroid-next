#!/bin/sh
# Read-only: what is libqtwpe.so (Qt WPE integration) and what else lives next to it?
echo "== find libqtwpe"
for p in /usr/lib64/libqtwpe.so* /usr/lib64/libsailfishbrowser.so* /usr/lib64/wpe-compat/*.so*; do
    [ -e "$p" ] || continue
    printf '## %s size=%s real=%s pkg=%s\n' "$p" "$(stat -c %s "$p")" \
        "$(readlink -f "$p" | xargs -r stat -c %s 2>/dev/null)" "$(rpm -qf "$p" 2>/dev/null | head -1)"
done
echo "== NEEDED: libqtwpe"
readelf -d /usr/lib64/libqtwpe.so.1 2>/dev/null | grep NEEDED
echo "== Qt NEEDED count in libqtwpe:"
readelf -d /usr/lib64/libqtwpe.so.1 2>/dev/null | grep -c libQt5 || true
echo "== libqtwpe exports: flat C (no C++ mangling in the name)"
nm -D --defined-only /usr/lib64/libqtwpe.so.1 2>/dev/null | grep -vE ' _Z' | head -30
echo "== libqtwpe exports mentioning renderer/host/target/egl/wpe"
nm -D --defined-only /usr/lib64/libqtwpe.so.1 2>/dev/null | grep -iE 'renderer|host|target|egl|wpe_' | head -30
echo "== total exports libqtwpe: $(nm -D --defined-only /usr/lib64/libqtwpe.so.1 2>/dev/null | wc -l)"
echo "== wpe-compat directory listing"
ls -l /usr/lib64/wpe-compat/ 2>/dev/null | head -30
