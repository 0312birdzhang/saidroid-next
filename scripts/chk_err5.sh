#!/bin/bash
grep -B3 -A5 "error:" /tmp/art-build5.log 2>/dev/null | head -30
