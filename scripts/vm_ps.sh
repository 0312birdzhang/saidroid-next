ps -eo pid,etime,pcpu,rss,comm,args --sort=-pcpu | grep -E "dalvikvm|dex2oat|gdb" | grep -v grep | head -10
echo "=== art-data ==="
ls -R /tmp/art-data 2>/dev/null | head -20
