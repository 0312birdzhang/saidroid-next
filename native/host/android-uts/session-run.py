#!/usr/bin/python3
"""Run an ordinary command through the matching private Android UTS session."""
import argparse
import array
import json
import os
from pathlib import Path
import socket
import struct
import sys


def receive(connection):
    raw, _, flags, _ = connection.recvmsg(65536)
    if not raw or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
        raise RuntimeError("truncated or missing session response")
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command or not os.path.isabs(command[0]) or os.getuid() == 0 or os.geteuid() != os.getuid():
        parser.error("an absolute command and ordinary caller are required")
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    try:
        connection.settimeout(5)
        connection.connect(args.socket)
        _, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")))
        if uid != os.getuid() or gid != os.getgid():
            raise PermissionError("actual session peer UID/GID differs")
        value = dict(operation="exec", argv=command, cwd=os.getcwd(), env=dict(os.environ))
        raw = json.dumps(value, separators=(",", ":")).encode()
        if len(raw) > 65536:
            raise ValueError("bounded request exceeds 64KiB")
        descriptors = array.array("i", [0, 1, 2])
        if connection.sendmsg([raw], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, descriptors)]) != len(raw):
            raise OSError("incomplete bounded exec request")
        started = receive(connection)
        if started.get("type") != "started" or started.get("uid") != os.getuid() or started.get("hostname") != "localhost" or started.get("no_new_privs") != 1 or started.get("capabilities") != 0:
            raise RuntimeError("ordinary Android session failed: " + str(started))
        connection.settimeout(None)
        try:
            finished = receive(connection)
        except KeyboardInterrupt:
            connection.send(json.dumps(dict(operation="cancel")).encode())
            connection.settimeout(5)
            finished = receive(connection)
        if finished.get("type") != "finished" or finished.get("cleanup") is not True or not isinstance(finished.get("code"), int):
            raise RuntimeError("command completion failed: " + str(finished))
        code = finished["code"]
        return code if code >= 0 else 128 - code
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("SD_ANDROID_UTS_RUN=failed|" + str(error), file=sys.stderr)
        sys.exit(125)
