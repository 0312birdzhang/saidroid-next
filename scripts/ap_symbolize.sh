#!/bin/bash
# 从 gdb 日志的 mappings 里找出故障地址属于哪个库，并离线符号化
# info proc mappings 列：Start End Size Offset Perms objfile
LOG=/tmp/ap/gdb.log
PC=$1
line=$(awk -v pc="$PC" '
  /Mapped address spaces/ { inmap=1; next }
  inmap && /^ *0x/ {
    s=strtonum($1); e=strtonum($2); p=strtonum(pc);
    if (p>=s && p<e) { print $1, $2, $4, $6; exit }
  }
' $LOG)
if [ -z "$line" ]; then echo "未找到映射"; exit 1; fi
for w in $line; do :; done
start=$(echo $line | cut -d' ' -f1)
end=$(echo $line | cut -d' ' -f2)
off=$(echo $line | cut -d' ' -f3)
path=$(echo $line | cut -d' ' -f4)
pcd=$((16#${PC#0x})); std=$((16#${start#0x})); offd=$((16#${off#0x}))
fileoff=$(( pcd - std + offd ))
echo "映射: $start - $end  段偏移=$off"
echo "库: $path"
printf "文件内偏移 = 0x%x\n" $fileoff
[ -f "$path" ] || { echo "库文件不在"; exit 1; }
echo "=== 最近的已定义符号 ==="
nm -C --defined-only "$path" 2>/dev/null | awk -v t=$fileoff '
  { a=strtonum("0x"$1) }
  a<=t { last=$0; la=a }
  END { if (last!="") { n=split(last,f," "); printf "  0x%x  %s  (+0x%x)\n", la, f[3], t-la } }'
echo "=== addr2line ==="
addr2line -f -C -e "$path" $fileoff 2>/dev/null | head -4
