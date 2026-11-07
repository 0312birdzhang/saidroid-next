#!/bin/sh
STUB=/var/tmp/sd-hostabi/libegl-stubs.so
echo "== exports count: $(nm -D --defined-only $STUB | wc -l)"
nm -D --defined-only "$STUB" | awk '{print $2, $3}' | head -40
echo "== strings: protocol-ish =="
strings -a "$STUB" | grep -iE 'socket|shm|proto|command|dlsym|dummy|noop|stub|fake|hub|host|renderer' | head -25
echo "== undefined (what it needs at runtime) =="
nm -D --undefined-only "$STUB" | head -20
