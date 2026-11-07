#!/usr/bin/env python3
"""Bounded, loopback-only test transport over the existing authenticated SSH link.

This forwards original public TCP endpoints byte-for-byte. It does not parse TLS,
install certificates, rewrite DNS replies, impersonate servers, or change routes.
Run in MeeGo Build; stop with its owned stop file or its absolute deadline.
"""
from pathlib import Path
import argparse, concurrent.futures, ipaddress, json, os, select, socket, struct
import subprocess, threading, time, hashlib


def read_exact(connection, size):
    result = b''
    while len(result) < size:
        data = connection.recv(size - len(result))
        if not data:
            raise EOFError('Truncated SOCKS request')
        result += data
    return result


def public_addresses(host, port):
    if port not in (80, 443):
        raise ValueError('Relay permits only original HTTP/TLS ports')
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    usable = []
    for family, kind, protocol, _, address in addresses:
        # A resolved private/local target must not become a route into the VM.
        if ipaddress.ip_address(address[0]).is_global:
            item = (family, kind, protocol, address)
            if item not in usable:
                usable.append(item)
    if not usable:
        raise ValueError('Relay permits public Internet targets only')
    return usable


def serve(connection, address, deadline, record, stop_event=None):
    remote = None
    connected = False
    host = None
    port = None
    try:
        if address[0] != '127.0.0.1':
            raise ValueError('Only the local SSH tunnel may use the relay')
        connection.settimeout(8)
        version, methods = read_exact(connection, 2)
        if version != 5 or not methods or 0 not in read_exact(connection, methods):
            raise ValueError('Unsupported SOCKS authentication')
        connection.sendall(b'\x05\x00')
        version, command, reserved, kind = read_exact(connection, 4)
        if (version, command, reserved) != (5, 1, 0):
            raise ValueError('Only SOCKS5 TCP CONNECT is supported')
        if kind == 1:
            host = socket.inet_ntop(socket.AF_INET, read_exact(connection, 4))
        elif kind == 4:
            host = socket.inet_ntop(socket.AF_INET6, read_exact(connection, 16))
        elif kind == 3:
            host = read_exact(connection, read_exact(connection, 1)[0]).decode('ascii')
        else:
            raise ValueError('Unsupported SOCKS address')
        port = struct.unpack('!H', read_exact(connection, 2))[0]
        errors = []
        for family, kind, protocol, target in public_addresses(host, port):
            candidate = socket.socket(family, kind, protocol)
            candidate.settimeout(5)
            try:
                candidate.connect(target)
                remote = candidate
                break
            except OSError as error:
                errors.append(str(error))
                candidate.close()
        if remote is None:
            raise OSError('Public endpoint unavailable: ' + ','.join(errors))
        connection.sendall(b'\x05\x00\x00\x01' + b'\x00' * 6)
        connected = True
        connection.setblocking(False)
        remote.setblocking(False)
        counts = [0, 0]
        pending = {connection: bytearray(), remote: bytearray()}
        readable = {connection, remote}
        last = time.monotonic()
        while time.monotonic() < deadline and time.monotonic() - last < 60 and not (stop_event and stop_event.is_set()):
            readers = [p for p in readable if len(pending[remote if p is connection else connection]) < 262144]
            writers = [p for p, data in pending.items() if data]
            if not readers and not writers:
                break
            ready_read, ready_write, _ = select.select(readers, writers, [], 1)
            for source in ready_read:
                data = source.recv(65536)
                destination = remote if source is connection else connection
                if data:
                    pending[destination].extend(data)
                    counts[0 if source is connection else 1] += len(data)
                    last = time.monotonic()
                else:
                    readable.remove(source)
                    if not pending[destination]:
                        destination.shutdown(socket.SHUT_WR)
            for destination in ready_write:
                sent = destination.send(pending[destination])
                del pending[destination][:sent]
                source = remote if destination is connection else connection
                if not pending[destination] and source not in readable:
                    destination.shutdown(socket.SHUT_WR)
                if sent:
                    last = time.monotonic()
        record(dict(endpoint=host, port=port, client_bytes=counts[0], server_bytes=counts[1], tls='unmodified'))
    except (OSError, ValueError, EOFError) as error:
        try:
            if not connected:
                connection.sendall(b'\x05\x01\x00\x01' + b'\x00' * 6)
        except OSError:
            pass
        record(dict(endpoint=host, port=port, error=type(error).__name__, message=str(error)))
    finally:
        connection.close()
        if remote is not None:
            remote.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('evidence', type=Path)
    parser.add_argument('--expected-boot', required=True)
    parser.add_argument('--port', type=int, default=47151)
    parser.add_argument('--seconds', type=int, default=1800)
    args = parser.parse_args()
    assert 1024 <= args.port <= 65535 and 30 <= args.seconds <= 3600
    args.evidence.mkdir(exist_ok=False, parents=True)
    os.environ['SSHPASS'] = os.environ['SSHPASS']
    ssh = ['sshpass', '-e', 'ssh', '-o', 'ConnectTimeout=6', 'root@bonito']
    facts = subprocess.check_output(ssh + ['cat', '/etc/sailfish-release'], timeout=10).decode()
    boot = subprocess.check_output(ssh + ['cat', '/proc/sys/kernel/random/boot_id'], timeout=10).decode().strip()
    assert 'ID=sailfishos' in facts and boot == args.expected_boot
    owner = subprocess.check_output(ssh + ['cat', '/home/art/test/.device-lock/owner'], timeout=10).decode()
    assert owner.startswith('cts-module-run|'), 'Relay requires the active instrumentation transaction lock'
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(16)
    listener.settimeout(1)
    local_port = listener.getsockname()[1]
    stop = args.evidence / 'STOP'
    deadline = time.monotonic() + args.seconds
    lock = threading.Lock()

    def record(value):
        value['utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        with lock, (args.evidence / 'connections.jsonl').open('a') as output:
            output.write(json.dumps(value) + '\n')

    tunnel = None
    try:
        command = ssh[:-1] + ['-o', 'ExitOnForwardFailure=yes', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-N', '-R', f'127.0.0.1:{args.port}:127.0.0.1:{local_port}', ssh[-1]]
        with (args.evidence / 'ssh.log').open('w') as output:
            tunnel = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT)
        stop_event = threading.Event()
        slots = threading.BoundedSemaphore(16)
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            def accept_connections():
                while not stop_event.is_set():
                    try:
                        connection, address = listener.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        return
                    if not slots.acquire(blocking=False):
                        connection.close()
                        continue
                    def handle(connection=connection, address=address):
                        try:
                            serve(connection, address, deadline, record, stop_event)
                        finally:
                            slots.release()
                    pool.submit(handle)
            accepting = threading.Thread(target=accept_connections, daemon=True)
            accepting.start()
            try:
                # Verify this exact tunnel's SOCKS handshake from the phone,
                # without invoking an Android app or changing network settings.
                for _ in range(10):
                    assert tunnel.poll() is None, 'SSH reverse forwarding rejected'
                    body = f"import socket;s=socket.create_connection(('127.0.0.1',{args.port}),2);s.sendall(bytes([5,1,0]));assert s.recv(2)==bytes([5,0]);s.close()"
                    probe = subprocess.run(ssh + ['python3', '-'], input=body.encode(), capture_output=True, timeout=6)
                    if probe.returncode == 0:
                        break
                    time.sleep(.2)
                else:
                    raise RuntimeError('Phone loopback tunnel handshake unavailable')
                (args.evidence / 'ready.json').write_text(json.dumps(dict(boot=boot, phone_host='127.0.0.1', phone_port=args.port, vm_host='127.0.0.1', vm_port=local_port, deadline_seconds=args.seconds, pid=os.getpid(), tunnel_pid=tunnel.pid, relay_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), tls='unmodified', scope='temporary-test-process-transport'), indent=2) + '\n')
                while time.monotonic() < deadline and not stop.exists():
                    assert tunnel.poll() is None, 'SSH tunnel terminated'
                    stop_event.wait(1)
            finally:
                stop_event.set()
                listener.close()
                accepting.join(timeout=2)
    finally:
        listener.close()
        if tunnel is not None and tunnel.poll() is None:
            tunnel.terminate()
            try:
                tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.kill()
                tunnel.wait(timeout=5)
        (args.evidence / 'stopped.json').write_text(json.dumps(dict(tunnel_exit=tunnel.returncode if tunnel else None, listener_closed=True, boot=boot)) + '\n')


if __name__ == '__main__':
    main()
