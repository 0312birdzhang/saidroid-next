#!/bin/bash
echo "=== 现有 JDK ==="
ls -d /usr/lib/jvm/* 2>/dev/null
echo "=== 之前下载的 Temurin ==="
ls -d /tmp/jdkfull/* /tmp/jdk 2>/dev/null | head -3
echo "=== 谁占着 dpkg ==="
ps aux 2>/dev/null | grep -E "dpkg|apt" | grep -v grep | head -3
