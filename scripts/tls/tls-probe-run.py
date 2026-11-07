#!/usr/bin/env python3
"""Device-side runner: execute a Java probe against the deployed SailDroid runtime.

Replicates the exact command line that `saildroid-open` builds for `SdRuntime`
(same binary, same boot class path, same library path) but runs our own main class
and can add extra -D properties. Runs as the phone user so ART file access matches.

    python3 /home/art/test/tls-probe-run.py <main-class> <probe.jar> [extra -D ...]

Prints PROBE_CMD= so the invocation is auditable, then the probe's own output.
"""
import json
import os
import pwd
import subprocess
import sys

ROOT = os.path.realpath('/home/art/api29-root')
LOG_DIR = '/home/art/test'


def build_command(main_class, jar, extra_props):
    manifest = json.load(open(ROOT + '/runtime.json'))
    jars = []
    for relative in manifest['boot_jars']:
        path = os.path.normpath(os.path.join(ROOT, relative))
        if not os.path.exists(path):
            raise SystemExit('PROBE_FAIL=missing_boot_jar|' + path)
        if not path.startswith(ROOT + '/'):
            raise SystemExit('PROBE_FAIL=boot_jar_escaped|' + path)
        jars.append(path)
    command = [
        ROOT + '/libexec/saildroid-launch',
        '-Xnoimage-dex2oat',
        '-Xbootclasspath:' + ':'.join(jars),
        '-Djava.library.path=' + ROOT + '/android-libs:/home/art/lib',
        '-Dsaidroid.native.runtime=' + ROOT + '/android-libs',
    ]
    command.extend(extra_props)
    command.extend(['-cp', jar, main_class])
    return command


def main():
    if len(sys.argv) < 3:
        raise SystemExit('usage: tls-probe-run.py <main-class> <probe.jar> [extra -D ...]')
    main_class, jar = sys.argv[1], sys.argv[2]
    extra = sys.argv[3:]
    command = build_command(main_class, jar, extra)
    print('PROBE_CMD=' + ' '.join(command), flush=True)

    user = pwd.getpwnam('defaultuser')
    env = dict(os.environ)
    env.update(
        HOME=user.pw_dir,
        USER=user.pw_name,
        LOGNAME=user.pw_name,
        XDG_RUNTIME_DIR='/run/user/100000',
        DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket',
    )
    env.pop('SAILDROID_CONTROL_SOCKET', None)
    env.pop('SAILDROID_APP_LAUNCH_ID', None)
    result = subprocess.run(
        command, env=env, timeout=120,
        preexec_fn=lambda: (os.setgid(user.pw_gid), os.setuid(user.pw_uid)),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sys.stdout.write(result.stdout or '')
    print('PROBE_EXIT=' + str(result.returncode), flush=True)
    sys.exit(0 if result.returncode == 0 else 1)


if __name__ == '__main__':
    main()
