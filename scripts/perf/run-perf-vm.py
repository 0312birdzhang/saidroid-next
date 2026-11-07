#!/usr/bin/env python3
"""Drive one perf measurement run on the phone and pull the raw frame records.

Run inside the MeeGo Build VM, with the device lock held:

    python3 scripts/perf/run-perf-vm.py --tag qq-base --scenario qq --swipes 3
    python3 scripts/perf/run-perf-vm.py --tag scroll-heavy --scenario scroll \
        --mode heavy --window 12

What it does, in order (each step is a separate ssh call, the app keeps running):

 1. refuse to start if the package is already running;
 2. launch through the installed launcher (saildroid-open) with
    SAILDROID_PERF=1 + SAILDROID_PERF_FILE so the native window library samples
    the frame path; the launch path is the same one the desktop icon uses;
 3. wait for the first really drawn frame (SDSURFACE=buffer_committed) or the
    benchmark Activity's ready marker;
 4. warm up (default 4 s, discarded by the analyzer);
 5. optional screenshot through the shared sdtool (Lipstick saveScreenshot);
 6. optional real touch gestures through /home/art/bin/sdinput;
 7. close through the launcher, which lets the window thread flush its
    in-memory frame records to SAILDROID_PERF_FILE;
 8. pull the perf file + screenshot into build/perf/<tag>/.

CPU numbers come from /proc/<pid>/stat (utime+stime) and per-thread
/proc/<pid>/task/*/stat deltas around the same window, and log growth is the
byte delta of the ART log file; both quantify non-frame overhead (JNI lookup
warnings, SSL retry storms) without touching the process.
"""
from pathlib import Path
import argparse, json, os, subprocess, time

REPO = Path('/media/psf/Home/WorkSpace/saidroid-next')
OUT = REPO / 'build/perf'
SSH_BASE = ['sshpass', '-e', 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=8',
            'root@bonito']
SCP_BASE = ['sshpass', '-e', 'scp', '-o', 'StrictHostKeyChecking=no', '-O',
            '-o', 'ConnectTimeout=8']
ENV = dict(os.environ, SSHPASS=os.environ['SSHPASS'])
TOOL = '/home/art/bin/sdtool.py'
SDINPUT = '/home/art/bin/sdinput'

LAUNCH_AND_WAIT = r'''PKG=%(pkg)r
MARKER=%(marker)r
import json, os, pwd, subprocess, time
from pathlib import Path
state = Path('/run/user/100000/saildroid/' + PKG + '.json')
def read():
    try:
        return json.loads(state.read_text())
    except (OSError, ValueError):
        return None
before = read() or {}
old_launch = before.get('launch_id')
u = pwd.getpwnam('defaultuser')
env = dict(os.environ, HOME=u.pw_dir, USER=u.pw_name, LOGNAME=u.pw_name,
           XDG_RUNTIME_DIR='/run/user/100000',
           DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
env.update(%(extra_env)r)
log = '/home/art/test/perf-launch-%%s-%%d.log' %% (PKG, int(time.time()))
with open(log, 'ab') as stream:
    subprocess.Popen(['/home/art/bin/saildroid-open', '--package', PKG], stdout=stream,
                     stderr=subprocess.STDOUT, start_new_session=True, env=env,
                     user=u.pw_uid, group=u.pw_gid,
                     extra_groups=os.getgrouplist(u.pw_name, u.pw_gid))
print('LAUNCHED package=%%s log=%%s' %% (PKG, log))
deadline = time.monotonic() + 30
current = None
while time.monotonic() < deadline:
    current = read()
    if current and current.get('launch_id') != old_launch:
        break
    time.sleep(0.2)
else:
    raise SystemExit('launch did not produce a new launch_id: %%r' %% (current,))
launch_log = current.get('log') or log
print('LAUNCH_ID', current.get('launch_id'), 'state', current.get('state'), 'log', launch_log)
deadline = time.monotonic() + 45
while time.monotonic() < deadline:
    text = Path(launch_log).read_text(errors='replace') if Path(launch_log).exists() else ''
    if MARKER in text:
        print('READY marker=%%s' %% MARKER)
        break
    current = read()
    if current and current.get('launch_id') == old_launch:
        raise SystemExit('application record vanished')
    if current and current.get('state') == 'exited':
        raise SystemExit('application exited before the marker: %%r' %% (current,))
    time.sleep(0.25)
else:
    raise SystemExit('marker %%s not seen in %%s' %% (MARKER, launch_log))
def normalise(line):
    for token in ('SDSURFACE=', 'SDWINDOW='):
        index = line.find(token)
        if index >= 0:
            return line[index:]
    return None
marker_lines = [normalise(line) for line in Path(launch_log).read_text(errors='replace').splitlines()]
marker_lines = [line for line in marker_lines if line][:12]
print('MARKERS_JSON', json.dumps(marker_lines))
'''

SCENARIOS = {
    'qq': dict(package='com.tencent.mobileqq', marker='SDSURFACE=buffer_committed'),
    'scroll': dict(package='org.example.saildroid.perfscroll', marker='PERFSCROLL=ready'),
}


def ssh(command, timeout=40, env=None):
    r = subprocess.run(SSH_BASE + [command], capture_output=True, text=True, timeout=timeout,
                       env=env or ENV)
    return r


def ssh_py(body, timeout=60):
    r = subprocess.run(SSH_BASE + ['python3 -'], input=body.encode(), capture_output=True,
                       timeout=timeout, env=ENV)
    if r.returncode != 0:
        raise SystemExit('phone script failed rc=%d\n%s\n%s' % (r.returncode, r.stdout.decode(),
                                                               r.stderr.decode()[-2000:]))
    return r.stdout.decode()


def state_path(package):
    return '/run/user/100000/saildroid/%s.json' % package


def status(package):
    r = ssh('python3 %s --package %s status' % (TOOL, package), timeout=20)
    return r.stdout.strip()


def cpu_snapshot(package):
    body = ('PKG=%r\n' % package) + r'''
import json, time
from pathlib import Path
state = json.loads(Path('/run/user/100000/saildroid/' + PKG + '.json').read_text())
pid = state['pid']
def stat(path):
    raw = path.read_text()
    fields = raw[raw.rfind(') ') + 2:].split()
    return fields[0], int(fields[11]) + int(fields[12])
comm, ticks = stat(Path('/proc/%d/stat' % pid))
threads = {}
for task in Path('/proc/%d/task' % pid).iterdir():
    try:
        name, value = stat(task / 'stat')
    except (OSError, IndexError, ValueError):
        continue
    threads[task.name] = [name, value]
log = Path(state['log'])
print(json.dumps(dict(time=time.monotonic(), pid=pid, ticks=ticks, threads=threads,
                      log_bytes=log.stat().st_size if log.exists() else 0,
                      log=state['log'], state=state['state'])))
'''
    return json.loads(ssh_py(body, timeout=30))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--scenario', choices=sorted(SCENARIOS), required=True)
    ap.add_argument('--mode', default='heavy', help='PERFSCROLL_MODE for the scroll scenario')
    ap.add_argument('--driver', default='choreographer',
                    choices=['choreographer', 'handler', 'both', 'none'],
                    help='PERFSCROLL_DRIVER: isolate vsync delivery from pipeline throughput')
    ap.add_argument('--window', type=float, default=10.0, help='observation seconds after warmup')
    ap.add_argument('--warmup', type=float, default=4.0)
    ap.add_argument('--swipes', type=int, default=0, help='inject this many real swipes')
    ap.add_argument('--swipe-serve', action='store_true',
                    help='drive every swipe through ONE long-lived uinput device '
                         '(sdinput serve) instead of one device per gesture')
    ap.add_argument('--swipe-duration', type=int, default=1500)
    ap.add_argument('--swipe-steps', type=int, default=60)
    ap.add_argument('--swipe-gap', type=float, default=0.4,
                    help='pause between injected swipes (s); injection is paced, not bursty')
    ap.add_argument('--swipe-from', default='540,1700')
    ap.add_argument('--swipe-to', default='540,700')
    ap.add_argument('--shot', action='store_true')
    ap.add_argument('--keep-running', action='store_true')
    # Gate control: identical launch, same scenario, but SAILDROID_PERF unset so the
    # sampler code is inert. Used to show the instrumentation costs nothing.
    ap.add_argument('--no-perf', action='store_true')
    ap.add_argument('--env', action='append', default=[],
                    help='extra KEY=VALUE for the app environment (repeatable), e.g. '
                         '--env SAILDROID_NO_FASTPATH=1')
    args = ap.parse_args()

    scenario = SCENARIOS[args.scenario]
    package = scenario['package']
    marker = scenario['marker']
    tag = args.tag
    out = OUT / tag
    out.mkdir(parents=True, exist_ok=True)
    perf_remote = '/home/art/data/logs/%s/perf-%s.bin' % (package, tag)
    screen_remote = '/home/defaultuser/Downloads/SailDroid-Screenshots/%s.png' % tag

    running = status(package)
    if 'state=running' in running:
        raise SystemExit('refusing to measure: package already running\n' + running)
    ssh('rm -f ' + perf_remote, timeout=20)

    extra_env = {}
    if not args.no_perf:
        extra_env.update(SAILDROID_PERF='1', SAILDROID_PERF_FILE=perf_remote)
    if args.scenario == 'scroll':
        extra_env['PERFSCROLL_MODE'] = args.mode or 'heavy'
        extra_env['PERFSCROLL_DRIVER'] = args.driver
    for item in args.env:
        key, _, value = item.partition('=')
        if not key:
            raise SystemExit('--env needs KEY=VALUE, got %r' % item)
        extra_env[key] = value
    # Launch through the installed launcher with an explicit --package: scripts/sdtool.py
    # drops the flag for its default package and starts `saildroid-open` bare, which only
    # makes the launcher print its usage line. Wait for a *new* launch id so a stale
    # record from an earlier run can never be mistaken for this run's process.
    launch_out = ssh_py(LAUNCH_AND_WAIT % dict(pkg=package, marker=marker, extra_env=extra_env),
                        timeout=90)
    print(launch_out)
    launch_log = None
    for line in launch_out.splitlines():
        if line.startswith('LAUNCH_ID ') and ' log ' in line:
            launch_log = line.rsplit(' log ', 1)[1].strip()
    time.sleep(args.warmup)

    if args.shot:
        print(ssh('python3 %s --package %s shot %s' % (TOOL, package, tag), timeout=40).stdout.strip())

    launched_at = time.monotonic() - args.warmup

    def snapshot():
        """CPU counters of the app process, or None when it already exited.

        QQ calls System.exit(0) a few seconds after showing its login page; a run
        must still keep whatever frames the sampler streamed to disk instead of
        aborting on a vanished /proc entry.
        """
        try:
            return cpu_snapshot(package)
        except SystemExit:
            return None

    before = snapshot()
    gestures = []
    # The window is an observation window, not a sleep: with --swipes the gestures are
    # paced across it, because a burst of swipes says nothing about steady-state cost.
    deadline = time.monotonic() + args.window
    index = 0
    # sdinput takes FIVE separate numbers: `swipe X1 Y1 X2 Y2 [dur] [steps]`.
    # Passing "540,1700" made atoi() read x1=540 y1=540 and the gesture landed
    # somewhere else entirely (measured on device 2026-10-27).
    fx, fy = args.swipe_from.split(',')
    tx, ty = args.swipe_to.split(',')
    swipe = '%s %s %s %s %d %d' % (fx.strip(), fy.strip(), tx.strip(), ty.strip(),
                                   args.swipe_duration, args.swipe_steps)
    if args.swipe_serve and args.swipes:
        # One uinput device for the whole sequence. Every separate `sdinput swipe`
        # creates and destroys an input device, and lipstick's evdevtouch plugin
        # re-opens the touchscreen on each hotplug -- that churn is the prime
        # suspect for its SIGSEGV (2026-10-27). serve() sends the same events from
        # a single device, so the gesture evidence stops being entangled with it.
        script = ''.join('swipe %s\nsleep %d\n' % (swipe, int(args.swipe_gap * 1000))
                         for _ in range(args.swipes))
        r = subprocess.run(SSH_BASE + [SDINPUT + ' serve'], input=script,
                           capture_output=True, text=True, env=ENV,
                           timeout=max(60, args.swipes * (args.swipe_duration / 1000.0 + 30)))
        gestures.append(r.stdout.strip())
        index = args.swipes
    else:
        while time.monotonic() < deadline:
            if index < args.swipes:
                r = ssh('%s swipe %s' % (SDINPUT, swipe), timeout=30)
                gestures.append(r.stdout.strip())
                index += 1
                time.sleep(args.swipe_gap)
            elif args.swipes == 0:
                time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
            else:
                break
    # "Delivered" is what the injector can actually prove: every write() into the
    # uinput node returned the full struct. A line printed before the write only
    # proves intent -- that is how "SDINPUT=tap" looked successful while the events
    # went to a node no reader had opened yet. Whether the compositor then consumed
    # them is a separate claim, made by the frame counters (pump verdict), not here.
    swipes_delivered = sum(1 for line in '\n'.join(gestures).splitlines()
                           if 'SDINPUT=finished' in line and 'kind=swipe' in line
                           and 'errors=0' in line)
    swipes_handled = swipes_delivered
    after = snapshot()
    if before is None:
        after = None
    exited_early = before is None or after is None
    lifetime_seconds = round(time.monotonic() - launched_at, 2) if exited_early else None
    if exited_early:
        print('APP_EXITED_DURING_WINDOW', status(package))

    if not args.keep_running and not exited_early:
        print(ssh('python3 %s --package %s close' % (TOOL, package), timeout=45).stdout.strip())
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            text = status(package)
            if 'state=running' not in text and 'state=starting' not in text:
                print(text)
                break
            time.sleep(0.4)
        else:
            raise SystemExit('application did not close; perf records were not flushed')

    log_path = (after or {}).get('log') or launch_log
    app_log_local = None
    if log_path:
        target = out / 'app.log'
        r = subprocess.run(SCP_BASE + ['-q', 'root@bonito:' + log_path, str(target)],
                           env=ENV, timeout=120)
        if r.returncode == 0 and target.exists():
            app_log_local = str(target)
        else:
            print('APP_LOG_PULL_FAILED', log_path)
    if not args.no_perf:
        subprocess.run(SCP_BASE + ['-q', 'root@bonito:' + perf_remote,
                                   str(out / 'perf.bin')], check=True, env=ENV, timeout=60)
    if args.shot:
        r = subprocess.run(SCP_BASE + ['-q', 'root@bonito:' + screen_remote,
                                       str(out / 'screen.png')], env=ENV, timeout=60)
        print('SCREENSHOT_PULLED', 'yes' if r.returncode == 0 else 'no')

    log_lines_at_close = None
    if log_path:
        r = ssh('wc -l < %s' % log_path, timeout=20)
        try:
            log_lines_at_close = int(r.stdout.split()[0])
        except (ValueError, IndexError):
            log_lines_at_close = None
    ticks = os.sysconf('SC_CLK_TCK')
    thread_delta = {}
    if before is not None and after is not None:
        for tid, (name, value) in after['threads'].items():
            if tid in before['threads']:
                thread_delta[name] = thread_delta.get(name, 0) + (value - before['threads'][tid][1])
        seconds = after['time'] - before['time']
    else:
        seconds = args.window
    markers = []
    for line in launch_out.splitlines():
        if line.startswith('MARKERS_JSON '):
            markers = json.loads(line[len('MARKERS_JSON '):])
    have_counters = before is not None and after is not None
    meta = dict(tag=tag, scenario=args.scenario, mode=args.mode, package=package,
                markers=markers,
                perf_enabled=not args.no_perf,
                perf_remote=perf_remote, log=log_path,
                window_seconds=seconds,
                app_exited_early=exited_early,
                app_lifetime_seconds=lifetime_seconds,
                cpu_ms=(round((after['ticks'] - before['ticks']) * 1000.0 / ticks, 1)
                        if have_counters else None),
                cpu_percent_of_one_core=(round((after['ticks'] - before['ticks']) /
                                               max(seconds, 1e-9) / ticks * 100, 1)
                                         if have_counters else None),
                threads=dict(sorted(((k, round(v * 1000.0 / ticks, 1))
                                     for k, v in thread_delta.items()),
                                    key=lambda item: -item[1])[:12]),
                log_bytes_per_second=(round((after['log_bytes'] - before['log_bytes']) /
                                            max(seconds, 1e-9), 0) if have_counters else None),
                log_lines_at_close=log_lines_at_close,
                log_path=log_path,
                app_log_local=app_log_local,
                gestures=gestures,
                # Provenance of the motion in this window: injected = real uinput
                # gestures (sdinput), self = the Activity drives its own frames. Never
                # mix the two when comparing numbers.
                scene_driver='injected' if args.swipes > 0 else 'self',
                swipes_requested=args.swipes,
                swipes_handled=swipes_handled, swipes_delivered=swipes_delivered)
    (out / 'meta.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps(meta, indent=2))
    if not args.no_perf:
        print('PERF_FILE', out / 'perf.bin', (out / 'perf.bin').stat().st_size if
              (out / 'perf.bin').exists() else 'MISSING')


if __name__ == '__main__':
    main()
