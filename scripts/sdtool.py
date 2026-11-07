#!/usr/bin/env python3
"""SailDroid 设备侧共享工具（在 VM 里跑，以 defaultuser 身份操作运行时）。

三条线都要反复做同样几件事：启动应用、等窗口画出来、截图、看生命周期日志、关闭。
以前每个脚本各自拼一遍，容易踩错用户/总线环境。这里统一成一套命令。

用法（在 VM 里）：
    sdtool.py status [--package PKG]
    sdtool.py launch [--package PKG] [--wait 30]
    sdtool.py wait   [--package PKG] [--wait 30] [--marker TEXT]
    sdtool.py shot   <名字> [--dir DIR]
    sdtool.py log    [--package PKG] [-n 80]
    sdtool.py close  [--package PKG]

约定：
  * 运行用户 defaultuser(100000)，HOME=/home/defaultuser，
    XDG_RUNTIME_DIR=/run/user/100000，
    DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket
  * 运行时状态记录在 /run/user/100000/saildroid/<package>.json（含 state 与 log 路径）
  * 截图走 Lipstick 的 D-Bus：org.nemomobile.lipstick.saveScreenshot
  * 截图统一落在 /home/defaultuser/Downloads/SailDroid-Screenshots/
"""
import argparse
import json
import os
import pwd
import subprocess
import sys
import time
from pathlib import Path

ART_ROOT = Path('/home/art/api29-root')
OPEN = '/home/art/bin/saildroid-open'
SHOT_DIR = Path('/home/defaultuser/Downloads/SailDroid-Screenshots')
STATE_DIR = Path('/run/user/100000/saildroid')
DEFAULT_PKG = 'com.tencent.mobileqq'


def user_env():
    u = pwd.getpwnam('defaultuser')
    env = dict(os.environ)
    env.update(
        HOME=u.pw_dir,
        USER=u.pw_name,
        LOGNAME=u.pw_name,
        XDG_RUNTIME_DIR='/run/user/100000',
        DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket',
    )
    return u, env


def as_user_kwargs(u):
    return dict(user=u.pw_uid, group=u.pw_gid,
                extra_groups=os.getgrouplist(u.pw_name, u.pw_gid))


def state_path(pkg):
    return STATE_DIR / (pkg + '.json')


def launch_epoch_path(pkg):
    return Path('/home/art/test') / ('.sdtool-launch-' + pkg)


def read_state(pkg, fresh_since=None):
    """读运行态记录。

    fresh_since 不为 None 时，修改时间早于它的记录一律当作不存在：否则 wait 会把
    上一次已关闭实例留下的 exited 记录和旧日志误当成这一次的结果。
    """
    p = state_path(pkg)
    if not p.exists():
        return None
    try:
        if fresh_since is not None and p.stat().st_mtime < fresh_since:
            return None
        return json.loads(p.read_text())
    except Exception:
        return None


def read_launch_epoch(pkg):
    try:
        return float(launch_epoch_path(pkg).read_text().strip())
    except Exception:
        return None


def cmd_status(args):
    st = read_state(args.package)
    root = ART_ROOT.resolve()
    print('root=%s' % root)
    if not st:
        print('state=(没有运行记录)')
        return 1
    print('state=%s' % st.get('state'))
    print('pid=%s' % st.get('pid'))
    print('log=%s' % st.get('log'))
    if st.get('log') and Path(st['log']).exists():
        lines = Path(st['log']).read_text(errors='replace').splitlines()
        print('log_lines=%d' % len(lines))
    return 0


def cmd_log(args):
    st = read_state(args.package)
    if not st or not st.get('log'):
        print('没有日志', file=sys.stderr)
        return 1
    lines = Path(st['log']).read_text(errors='replace').splitlines()
    for line in lines[-args.n:]:
        print(line)
    return 0


def cmd_launch(args):
    u, env = user_env()
    logdir = Path('/home/art/test')
    logdir.mkdir(parents=True, exist_ok=True)
    log_path = logdir / ('sdtool-%s-%d.log' % (args.package, int(time.time())))
    with open(log_path, 'ab') as stream:
        # 必须显式 --package：裸 saildroid-open 只打印 usage，应用根本不会起来。
        launch_epoch = int(time.time())
        try:
            launch_epoch_path(args.package).write_text(str(launch_epoch))
        except Exception:
            pass
        # 旧实例的运行态记录必须失效，否则 wait 会读到上次的 exited 记录。
        try:
            state_path(args.package).unlink()
        except Exception:
            pass
        for item in getattr(args, 'env', []) or []:
            key, sep, value = item.partition('=')
            if not sep or not key:
                print('BAD_ENV %s' % item)
                return 2
            env[key] = value
        cmd = [OPEN, '--package', args.package]
        subprocess.Popen(cmd, stdout=stream, stderr=subprocess.STDOUT,
                         start_new_session=True, env=env, **as_user_kwargs(u))
    print('LAUNCHED package=%s log=%s' % (args.package, log_path))
    if args.wait > 0:
        return cmd_wait(args)
    return 0


def cmd_wait(args):
    deadline = time.monotonic() + args.wait
    fresh_since = read_launch_epoch(args.package)
    last = None
    while time.monotonic() < deadline:
        st = read_state(args.package, fresh_since=fresh_since)
        if st:
            last = st
            marker = getattr(args, 'marker', None)
            if marker:
                log = st.get('log')
                if log and Path(log).exists() and marker in Path(log).read_text(errors='replace'):
                    print('READY marker=%s' % marker)
                    return 0
            elif st.get('state') == 'running':
                print('READY state=running pid=%s' % st.get('pid'))
                return 0
        time.sleep(0.2)
    print('TIMEOUT last=%s' % last)
    return 1


def cmd_shot(args):
    outdir = Path(args.dir) if args.dir else SHOT_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    name = args.name if args.name.endswith('.png') else args.name + '.png'
    target = outdir / name
    u, env = user_env()
    # 旧的同名文件会影响判断：先删掉
    if target.exists():
        target.unlink()
    r = subprocess.run(
        ['gdbus', 'call', '--session', '--dest', 'org.nemomobile.lipstick',
         '--object-path', '/org/nemomobile/lipstick/screenshot',
         '--method', 'org.nemomobile.lipstick.saveScreenshot', str(target)],
        env=env, capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        print('SHOT_FAIL %s %s' % (r.returncode, (r.stderr or r.stdout).strip()), file=sys.stderr)
        return 1
    # saveScreenshot 是异步落盘，等文件稳定
    deadline = time.monotonic() + 8
    size = -1
    while time.monotonic() < deadline:
        if target.exists():
            s = target.stat().st_size
            if s > 0 and s == size:
                print('SHOT_OK %s bytes=%d' % (target, s))
                return 0
            size = s
        time.sleep(0.25)
    print('SHOT_TIMEOUT %s' % target, file=sys.stderr)
    return 1


def cmd_close(args):
    u, env = user_env()
    r = subprocess.run([OPEN, '--package', args.package, '--close'],
                       env=env, capture_output=True, text=True, timeout=30,
                       **as_user_kwargs(u))
    out = (r.stdout + r.stderr).strip()
    print('CLOSE rc=%d %s' % (r.returncode, out))
    return 0 if r.returncode == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--package', default=DEFAULT_PKG)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('status'); p.set_defaults(func=cmd_status)
    p = sub.add_parser('log'); p.add_argument('-n', type=int, default=80); p.set_defaults(func=cmd_log)
    p = sub.add_parser('launch'); p.add_argument('--wait', type=int, default=0)
    p.add_argument('--env', action='append', default=[], metavar='KEY=VALUE',
                   help='额外环境变量，注入到 saildroid-open 的子进程（例：SAILDROID_ANDROID_LOG_STDERR=1）')
    p.set_defaults(func=cmd_launch)
    p = sub.add_parser('wait'); p.add_argument('--wait', type=int, default=30)
    p.add_argument('--marker'); p.set_defaults(func=cmd_wait)
    p = sub.add_parser('shot'); p.add_argument('name'); p.add_argument('--dir', default=None)
    p.set_defaults(func=cmd_shot)
    p = sub.add_parser('close'); p.set_defaults(func=cmd_close)

    args = ap.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
