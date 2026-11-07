#!/bin/bash
set -euo pipefail
cd /media/psf/Home/WorkSpace/saidroid-next
JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
gcc -fsyntax-only -Wall -I/tmp/jdkfull/jdk-21.0.13+9/include -I/tmp/jdkfull/jdk-21.0.13+9/include/linux \
  -I/var/tmp/saidroid-next-api29-product-r79 native/window/sdwindow.c && echo "SYNTAX_OK sdwindow.c"
