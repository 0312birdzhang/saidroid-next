echo "=== VM 侧 RNDIS 网卡 ==="
ip -o link show | grep -E "enx|rndis" | head -3
ip -o addr show | grep -E "192.168.2" | head -3
echo "=== ping 设备 ==="
ping -c 2 -W 2 bonito 2>&1 | tail -3
