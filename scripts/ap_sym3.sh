#!/bin/bash
LOG=/tmp/ap/gdb.log
PC=$1
line=$(awk -v pc="$PC" '
  /Mapped address spaces/ { inmap=1; next }
  inmap && /^ *0x/ { s=strtonum($1); e=strtonum($2); p=strtonum(pc);
    if (p>=s && p<e) { print $1, $2, $4, $6; exit } }' $LOG)
[ -z "$line" ] && { echo "$PC -> 没找到映射"; exit 1; }
start=$(echo $line|cut -d' ' -f1); off=$(echo $line|cut -d' ' -f3); path=$(echo $line|cut -d' ' -f4)
pva=$(readelf -lW "$path" 2>/dev/null | awk -v o=$((16#${off#0x})) '/LOAD/ {v=strtonum($3); f=strtonum($2); if (f==o){printf "0x%x",v; exit}}')
[ -z "$pva" ] && pva=0x0
vaddr=$(( $((16#${PC#0x})) - $((16#${start#0x})) + $((16#${pva#0x})) ))
printf "%s -> %s  vaddr=0x%x\n" "$PC" "$path" $vaddr
sym=$(nm --defined-only -C "$path" 2>/dev/null | awk -v t=$vaddr '{a=strtonum("0x"$1); if (a<=t){l=$0; la=a}} END {if(l!=""){n=split(l,f," "); printf "  0x%x  %s  (+0x%x)", la, substr(l,index(l,f[3])), t-la}}')
[ -z "$sym" ] && sym=$(nm -D --defined-only -C "$path" 2>/dev/null | awk -v t=$vaddr '{a=strtonum("0x"$1); if (a<=t){l=$0; la=a}} END {if(l!=""){n=split(l,f," "); printf "  0x%x  %s  (+0x%x)", la, substr(l,index(l,f[3])), t-la}}')
echo "$sym"
echo "  addr2line: $(addr2line -f -C -e "$path" $vaddr 2>/dev/null | tr '\n' ' ')"
