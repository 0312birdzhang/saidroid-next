#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH 'echo "=== 基于实测的推算 ==="
echo "样本: 3 dex / 28 MB → 19,345 类"
echo "QQ 总量: 40 dex / 389.8 MB"
echo ""
echo "类总数推算: 19345 / 28 * 389.8 ≈ 269,000 类"
echo "转换时间推算: 22s / 28 * 389.8 ≈ 306 秒（5分钟）"
echo "jar 大小推算: 假设 1.7KB/类 → 约 450 MB"
echo ""
echo "=== 设备存储 ==="
df -h / | tail -1
df -h /tmp | tail -1
echo ""
echo "=== 关键约束 ==="
echo "根分区剩余 2.6 GB，jar 需要约 450 MB —— 空间够"
echo "但 40 个 dex 转换产物要全部装进一个 jar 才能加载"'
