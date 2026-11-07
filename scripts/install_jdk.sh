#!/bin/bash
echo "=== 安装 OpenJDK ==="
apt-get install -y openjdk-17-jdk-headless 2>&1 | tail -8
echo "=== 验证 ==="
java -version 2>&1 | head -3
javac -version 2>&1 | head -2
