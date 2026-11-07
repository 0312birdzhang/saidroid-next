echo "=== recent dirs in /tmp ==="
ls -dlh --time-style=+%m-%d_%H:%M /tmp/*/ 2>/dev/null | sort -k6 | tail -25
echo "=== and23 ==="
ls /tmp/and23 2>/dev/null
echo "=== bio2 count ==="
ls /tmp/and23/bio2 | wc -l
echo "=== android lib dirs ==="
ls -d /tmp/and23/*/ 2>/dev/null
