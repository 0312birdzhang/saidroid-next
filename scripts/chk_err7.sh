#!/bin/bash
grep -B2 -A6 "error:" /tmp/art-build7.log 2>/dev/null | head -22
