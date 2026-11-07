#!/bin/bash
# 用 gdb.log 的 mappings 把一个运行时地址符号化（正确处理 p_vaddr/p_offset）
LOG=/tmp/ap/gdb.log
PC=$1
line=$(awk -v pc="$PC" '
  /Mapped address spaces/ { inmap=1; next }
  inmap && /^ *0x/ {
    s=strtonum($1); e=strtonum($2); p=strtonum(pc);
    if (p>=s && p<e) { print $1, $2, $4, $6; exit }
  }
' $LOG)
[ -z "$line" ] && { echo "没找到映射"; exit 1; }
start=$(echo $line | cut -d' ' -f1); off=$(echo $line | cut -d' ' -f3); path=$(echo $line | cut -d' ' -f4)
echo "映射 start=$start offset=$off path=$path"
[ -f "$path" ] || { echo "库不在"; exit 1; }
# 找出 file offset == $off 的那个 PT_LOAD 的 p_vaddr
pva=$(readelf -lW "$path" 2>/dev/null | awk -v o=$((16#${off#0x})) '
  /LOAD/ { v=strtonum($3); f=strtonum($2); if (f==o) { printf "0x%x", v; exit } }')
[ -z "$pva" ] && pva=0x0
pcd=$((16#${PC#0x})); sd=$((16#${start#0x})); pad=$((16#${pva#0x}))
vaddr=$(( pcd - sd + pad ))
printf "vaddr = 0x%x (段 p_vaddr=%s)\n" $vaddr $pva
echo "=== 最近的导出符号 ==="
nm -D --defined-only -C "$path" 2>/dev/null | awk -v t=$vaddr '
  { a=strtonum("0x"$1); if (a<=t) { last=$0; la=a } }
  END { if (last!="") { n=split(last,f," "); printf "  0x%x  %s  (+0x%x)\n", la, substr(last, index(last,f[3])), t-la } }'
echo "=== addr2line ==="
addr2line -f -C -e "$path" $vaddr 2>/dev/null | head -3
