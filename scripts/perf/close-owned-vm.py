#!/usr/bin/env python3
"""Close every SailDroid-owned application on the phone (installer, broker, apps).

Run inside the MeeGo Build VM while holding the device lock. A component update
refuses to run while any owned ART/supervisor process is alive, so this is the
supported way to clear the device before deploying.

    python3 scripts/perf/close-owned-vm.py
"""
import subprocess, os, json, time

SSH_BASE = ['sshpass', '-e', 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=8',
            'root@bonito']
ENV = dict(os.environ, SSHPASS=os.environ['SSHPASS'])
BODY = r'''
import json, os, pwd, subprocess, time, signal
from pathlib import Path
account = pwd.getpwnam('defaultuser')
env = dict(os.environ, HOME=account.pw_dir, USER=account.pw_name, LOGNAME=account.pw_name,
           XDG_RUNTIME_DIR='/run/user/100000',
           DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
kw = dict(user=account.pw_uid, group=account.pw_gid,
          extra_groups=os.getgrouplist(account.pw_name, account.pw_gid))
runtime = Path('/run/user/100000/saildroid')
boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def alive(record):
    try:
        pid = record.get('pid')
        if not isinstance(pid,int) or pid<=1 or record.get('boot')!=boot:return False
        proc=Path('/proc')/str(pid);raw=(proc/'stat').read_text();parts=raw[raw.rfind(') ')+2:].split()
        if parts[0]in ('Z','X') or int(parts[19])!=record['start_ticks']:return False
        uid=int(next(line for line in (proc/'status').read_text().splitlines() if line.startswith('Uid:')).split()[1])
        return uid==account.pw_uid
    except (KeyError, TypeError, ValueError, OSError):
        return False
for record_file in sorted(runtime.glob('*.json'),key=lambda p:p.name=='org.saildroid.binder.json'):
    try:
        record = json.loads(record_file.read_text())
    except (OSError, ValueError):
        continue
    name = record.get('package')
    if not name:
        continue
    state = record.get('state')
    pid = record.get('pid')
    running = alive(record)
    if not running:
        continue
    if name == 'org.saildroid.manager':
        command = ['/home/art/bin/saildroid-open', '--manager', '--close']
    elif name == 'org.saildroid.binder':
        command = ['/home/art/bin/saildroid-open', '--broker', '--close']
    elif record.get('role')=='service':
        command = ['/home/art/bin/saildroid-open', '--package', name, '--service',
                   record.get('service') or name, '--process', record['process_name'], '--close']
    else:
        command = ['/home/art/bin/saildroid-open', '--package', name, '--close']
    if record.get('schema')==3:
        command[0]=record['component']+'/libexec/saildroid-app'
    try:
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=40, **kw)
        print('CLOSE', name, 'rc=' + str(result.returncode), (result.stdout + result.stderr).strip()[:200])
        failed = result.returncode != 0
    except subprocess.TimeoutExpired:
        if name != 'org.saildroid.binder':
            raise
        failed = True
        print('CLOSE', name, 'timeout=40')
    # A broker whose session bus has already ended cannot answer its close RPC.
    # Recheck its full owned identity immediately before a graceful fallback.
    if failed and name == 'org.saildroid.binder' and alive(record):
        proc = Path('/proc') / str(pid)
        component = Path(record['component'])
        expected = component / 'libexec/saildroid-host'
        assert component.parent in (Path('/home/art/releases'), Path('/opt/saildroid/releases'))
        assert component.resolve() == component and not component.is_symlink()
        assert expected.stat().st_uid == 0 and expected.is_file()
        assert (proc / 'exe').resolve() == expected
        assert (proc / 'cmdline').read_bytes().split(b'\0', 1)[0].strip() == b'org.saildroid.binder'
        assert alive(record)
        os.kill(pid, signal.SIGTERM)
        print('CLOSE_BROKER_TERM', pid, 'start_ticks=' + str(record['start_ticks']))
# The native session manager is stopped only after every host has exited.
manager=runtime/'host-manager.state'
if manager.exists():
    identity=json.loads(manager.read_text())
    if alive(identity):
        expected=Path(identity['component'])/'libexec/saildroid-host'
        if (Path('/proc')/str(identity['pid'])/'exe').resolve()!=expected:raise RuntimeError('Native manager executable differs')
        os.kill(identity['pid'],signal.SIGTERM)
        print('CLOSE_NATIVE_MANAGER',identity['pid'])
deadline = time.monotonic() + 20
while time.monotonic() < deadline:
    remaining = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            command = (process / 'cmdline').read_bytes()
            executable = os.readlink(process / 'exe')
            if executable == '/home/art/bin/dalvikvm' or (executable.startswith(('/home/art/releases/', '/opt/saildroid/releases/')) and executable.endswith('/libexec/saildroid-host')) or b'api29-root/lib/runtime.jar' in command \
                    or b'api29-root/libexec/saildroid-open' in command \
                    or command.startswith((b'org.saildroid.manager\0', b'saildroid-supervisor:')):
                remaining.append(process.name)
        except (OSError, PermissionError):
            pass
    if not remaining:
        print('OWNED_PROCESSES=none')
        break
    time.sleep(0.5)
else:
    print('OWNED_PROCESSES=still-running', remaining)
    raise SystemExit(1)
'''


def main():
    r = subprocess.run(SSH_BASE + ['python3 -'], input=BODY.encode(), capture_output=True,
                       env=ENV, timeout=180)
    print(r.stdout.decode().strip())
    print(r.stderr.decode().strip()[-800:])
    r.check_returncode()


if __name__ == '__main__':
    main()
