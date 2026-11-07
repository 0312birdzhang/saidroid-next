#!/bin/bash
P=/var/tmp/saidroid-next-api29-product-perf-perf7
rm -rf /tmp/j7x && mkdir -p /tmp/j7x && cd /tmp/j7x && unzip -qo $P/runtime.jar
for name in locks unlocks draws composeEraseNs fastPathFrames composeRequests; do
  n=$(strings classes.dex | grep -cx "$name" || true)
  echo "$name -> $n"
done
strings classes.dex | grep -c "SdSurfaceStore"
