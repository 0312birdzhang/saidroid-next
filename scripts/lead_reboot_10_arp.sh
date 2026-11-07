#!/bin/bash
set -u
echo "### ifaces"; ip -4 addr show | grep -E "^[0-9]+:|inet " | head -20
echo "### route_192"; ip route get bonito 2>&1
echo "### arping"; (command -v arping >/dev/null && arping -c 2 -I $(ip route get bonito | grep -o "dev [^ ]*" | cut -d" " -f2) bonito) 2>&1 | tail -5
echo "### neigh"; ip neigh show 2>/dev/null | head
echo "### ping_from_route_iface"; ping -c 2 -W 2 bonito 2>&1 | tail -2
echo "### ports"
for p in 22 80 443 8080; do timeout 2 bash -c "cat < /dev/null > /dev/tcp/bonito/$p" 2>/dev/null && echo "$p OPEN" || echo "$p closed"; done
