#!/bin/bash
grep -A3 "fake_log_device.c:.*error" /tmp/art-build3.log 2>/dev/null | head -25
