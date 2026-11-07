#!/bin/bash
grep -E "cannot find|undefined reference" /tmp/art-build14.log 2>/dev/null | head -10
