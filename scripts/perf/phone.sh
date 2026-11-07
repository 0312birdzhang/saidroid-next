#!/bin/bash
# Run a shell snippet on the phone: the snippet is the first argument, or the
# contents of the file named as the first argument. prlctl re-splits argv, so
# anything non-trivial belongs in a file.
set -u
if [ -f "$1" ]; then cmd="$(cat "$1")"; else cmd="$1"; fi
SSHPASS="${SSHPASS:?Set SSHPASS for device development}" exec sshpass -e ssh -o StrictHostKeyChecking=no \
  -o ConnectTimeout=8 root@bonito "$cmd"
