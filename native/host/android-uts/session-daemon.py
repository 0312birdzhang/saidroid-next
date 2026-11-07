#!/usr/bin/python3
"""Ordinary-user command sessions inside an already configured Android UTS namespace.

This process has no privileged operation or service account. A root-owned startup
unit creates UTS through session-entry-host, then permanently drops to this UID.
The socket passes ordinary callers' stdio descriptors; it never reads credentials
or changes global host/network settings. This is not per-APK UID isolation.
"""
import argparse
import array
import ctypes
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import stat
import struct
import subprocess
import sys
import time

MAX_PACKET = 65536
MAX_JOBS = 8


def identity():
    uid = os.getuid()
    if not uid or os.geteuid() != uid or os.getgid() != os.getegid():
        raise PermissionError("ordinary process identity required")
    fields = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    if any(int(fields[name].strip(), 16) for name in ("CapEff", "CapPrm", "CapInh")):
        raise PermissionError("zero capability sets required")
    if ctypes.CDLL(None).prctl(39, 0, 0, 0, 0) != 1:
        raise PermissionError("kernel no_new_privs required")
    uname = os.uname()
    domain = Path("/proc/sys/kernel/domainname").read_text().strip()
    if uname.nodename != "localhost" or domain != "localdomain":
        raise RuntimeError("canonical Android UTS startup required")
    return dict(uid=uid, gid=os.getgid(), hostname=uname.nodename, domainname=domain,
                uts=os.readlink("/proc/self/ns/uts"), userns=os.readlink("/proc/self/ns/user"),
                net=os.readlink("/proc/self/ns/net"), no_new_privs=1, capabilities=0)


def send(connection, value):
    raw = json.dumps(value, separators=(",", ":")).encode()
    if len(raw) > MAX_PACKET or connection.send(raw) != len(raw):
        raise OSError("bounded reply failed")


def process_record(pid):
    path = Path("/proc") / str(pid)
    fields = (path / "stat").read_text().rsplit(") ", 1)[1].split()
    status = dict(line.split(":", 1) for line in (path / "status").read_text().splitlines() if ":" in line)
    try:
        uts = os.readlink(path / "ns/uts")
    except (PermissionError, FileNotFoundError):
        # A nondumpable ordinary app may hide its namespace link from its own
        # UID. Kernel UID/session/group/start time remain the ownership boundary.
        uts = None
    return dict(pid=pid, start_ticks=int(fields[19]), pgrp=int(fields[2]), session=int(fields[3]),
                uid=[int(v) for v in status["Uid"].split()], state=fields[0], uts=uts)


def family(job, own_identity):
    members = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            row = process_record(int(path.name))
        except (OSError, ValueError, ProcessLookupError):
            continue
        if row["pgrp"] == job["pid"] and row["session"] == job["pid"]:
            if row["uid"] != [own_identity["uid"]] * 4:
                raise PermissionError("owned command session identity changed")
            if row["pid"] == job["pid"] and row["start_ticks"] != job["start_ticks"]:
                raise PermissionError("command PID reused")
            if row["state"] != "Z":
                members.append(row)
    return members


def terminate_family(job, own_identity):
    # New sessions cannot be joined by unrelated processes from another session.
    # Check real UID, UTS, session, group and leader start time before signaling.
    for sig, duration in ((signal.SIGTERM, 1.0), (signal.SIGKILL, 1.0)):
        if not family(job, own_identity):
            return
        try:
            os.killpg(job["pid"], sig)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            if not family(job, own_identity):
                return
            time.sleep(.02)
    if family(job, own_identity):
        raise RuntimeError("owned command family cleanup incomplete")


def reap_extra_children(main_pid):
    deadline = time.monotonic() + 2
    while True:
        children = [int(v) for v in Path("/proc/self/task/" + str(os.getpid()) + "/children").read_text().split() if int(v) != main_pid]
        if not children:
            return
        for pid in children:
            try:
                os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                pass
        if time.monotonic() >= deadline:
            raise RuntimeError("adopted command children not reaped")
        time.sleep(.02)


def request(connection, own_identity):
    descriptors = []
    child = None
    job = None
    try:
        connection.settimeout(5)
        raw, ancillary, flags, _ = connection.recvmsg(MAX_PACKET, socket.CMSG_SPACE(16 * array.array("i").itemsize))
        for level, kind, data in ancillary:
            if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                values = array.array("i")
                values.frombytes(data[:len(data) - len(data) % values.itemsize])
                descriptors.extend(values)
            else:
                raise ValueError("unsupported ancillary data")
        if flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC) or not raw:
            raise ValueError("truncated or empty bounded request")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("object request required")
        if value == {"operation": "identity"}:
            if descriptors:
                raise ValueError("identity request has no descriptors")
            send(connection, dict(type="identity", pid=os.getpid(), **own_identity))
            return
        if set(value) != {"operation", "argv", "cwd", "env"} or value["operation"] != "exec" or len(descriptors) != 3:
            raise ValueError("exec request requires exactly three stdio descriptors")
        argv, cwd, env = value["argv"], value["cwd"], value["env"]
        if (not isinstance(argv, list) or not 1 <= len(argv) <= 256
                or any(not isinstance(v, str) or "\0" in v for v in argv)
                or not os.path.isabs(argv[0]) or not isinstance(cwd, str) or "\0" in cwd or not os.path.isabs(cwd)):
            raise ValueError("bounded absolute executable and cwd required")
        if (not isinstance(env, dict) or len(env) > 256
                or any(not isinstance(k, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", k)
                       or not isinstance(v, str) or "\0" in v for k, v in env.items())):
            raise ValueError("bounded string environment required")
        child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=descriptors[0], stdout=descriptors[1],
                                 stderr=descriptors[2], close_fds=True, start_new_session=True)
        job = process_record(child.pid)
        if job["uid"] != [own_identity["uid"]] * 4 or job["session"] != child.pid or job["pgrp"] != child.pid:
            raise PermissionError("actual ordinary command identity differs")
        send(connection, dict(type="started", job=job, **own_identity))
        for fd in descriptors:
            os.close(fd)
        descriptors.clear()
        connection.settimeout(None)
        while child.poll() is None:
            readable, _, _ = select.select([connection], [], [], .05)
            if readable:
                message = connection.recv(MAX_PACKET)
                if not message:
                    terminate_family(job, own_identity)
                    child.wait(timeout=3)
                    reap_extra_children(child.pid)
                    return
                control = json.loads(message)
                if control != {"operation": "cancel"}:
                    raise ValueError("only cancel is accepted during execution")
                terminate_family(job, own_identity)
                child.wait(timeout=3)
                reap_extra_children(child.pid)
                send(connection, dict(type="finished", code=child.returncode, cancelled=True, cleanup=True))
                return
        code = child.wait()
        terminate_family(job, own_identity)
        reap_extra_children(child.pid)
        send(connection, dict(type="finished", code=code, cancelled=False, cleanup=True))
    except BaseException as error:
        try:
            send(connection, dict(type="error", error=type(error).__name__, message=str(error)))
        except OSError:
            pass
    finally:
        for fd in descriptors:
            os.close(fd)
        if child is not None:
            if job is None:
                try:
                    child.terminate()
                except ProcessLookupError:
                    pass
            else:
                terminate_family(job, own_identity)
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
            reap_extra_children(child.pid)
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", required=True, type=Path)
    args = parser.parse_args()
    own_identity = identity()
    parent = args.socket.parent
    info = parent.lstat()
    if not stat.S_ISDIR(info.st_mode) or parent.is_symlink() or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise PermissionError("private ordinary-user socket directory required")
    if args.socket.exists() or args.socket.is_symlink():
        raise FileExistsError("existing socket path will not be replaced")
    if ctypes.CDLL(None).prctl(36, 1, 0, 0, 0):
        raise OSError("child subreaper required")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    children = {}
    stopping = False

    def stop(_signal, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        listener.bind(str(args.socket))
        args.socket.chmod(0o600)
        socket_identity = (args.socket.stat().st_dev, args.socket.stat().st_ino)
        listener.listen(MAX_JOBS)
        listener.settimeout(.2)
        print("SD_ANDROID_UTS_SESSION=" + json.dumps(dict(type="ready", pid=os.getpid(), **own_identity)), flush=True)
        while not stopping:
            while True:
                try:
                    pid, _ = os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    pid = 0
                if not pid:
                    break
                children.pop(pid, None)
            try:
                connection, _ = listener.accept()
            except socket.timeout:
                continue
            try:
                peer_pid, peer_uid, peer_gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")))
                if peer_uid != os.getuid() or peer_gid != os.getgid():
                    send(connection, dict(type="error", error="PermissionError", message="actual peer UID/GID differs"))
                    connection.close()
                    continue
                if len(children) >= MAX_JOBS:
                    send(connection, dict(type="error", error="Busy", message="bounded concurrent command limit"))
                    connection.close()
                    continue
                pid = os.fork()
                if pid == 0:
                    listener.close()
                    def interrupted(_signal, _frame):
                        raise InterruptedError("session controller stopping")
                    signal.signal(signal.SIGTERM, interrupted)
                    signal.signal(signal.SIGINT, interrupted)
                    if ctypes.CDLL(None).prctl(1, signal.SIGTERM, 0, 0, 0):
                        os._exit(125)
                    ctypes.CDLL(None).prctl(36, 1, 0, 0, 0)
                    request(connection, own_identity)
                    os._exit(0)
                children[pid] = process_record(pid)
                connection.close()
            except BaseException:
                connection.close()
                raise
    finally:
        listener.close()
        for pid, record in children.items():
            try:
                if process_record(pid)["start_ticks"] == record["start_ticks"]:
                    os.kill(pid, signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
        deadline = time.monotonic() + 8
        while children and time.monotonic() < deadline:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid:
                children.pop(pid, None)
            else:
                time.sleep(.02)
        for pid, record in children.items():
            try:
                if process_record(pid)["start_ticks"] == record["start_ticks"]:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
            except (OSError, ProcessLookupError, ChildProcessError):
                pass
        if "socket_identity" in locals() and args.socket.exists() and (args.socket.stat().st_dev, args.socket.stat().st_ino) == socket_identity:
            args.socket.unlink()


if __name__ == "__main__":
    main()
