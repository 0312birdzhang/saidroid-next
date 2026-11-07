L=/tmp/ap/ctx.log
echo "=== Binder / Parcel 注册结果 ==="
grep -a "register_android_os_Binder\|register_android_os_Parcel\|registered=" $L | head -6
echo "=== 所有注册行 ==="
grep -a "SDBRIDGE reg " $L | sed 's/.*reg _[A-Za-z0-9]*//' | head -50
