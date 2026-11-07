#!/bin/bash
set -euo pipefail
repo=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
work=$(mktemp -d /var/tmp/saildroid-host-manager-test.XXXXXX)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/libexec" /run/user/0
chmod 700 /run/user/0
g++ -std=c++17 -O2 -Wall -o "$work/libexec/saildroid-host" "$repo/native/host/tests/manager-fixture.cpp" "$repo/native/host/host-manager.cpp" $(pkg-config --cflags --libs gio-2.0) -pthread
dbus-run-session -- python3 "$repo/native/host/tests/test-manager.py" "$work"
