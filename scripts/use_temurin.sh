#!/bin/bash
echo "=== 用已有的 Temurin JDK 21 ==="
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
java -version 2>&1 | head -3
echo
echo "=== 但构建要求 openjdk 字样，检查 ==="
java -version 2>&1 | grep -i openjdk | head -2
