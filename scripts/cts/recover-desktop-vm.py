#!/usr/bin/env python3
"""Explicitly authorized recovery of an unresponsive Lipstick event loop.

Requires --restart-desktop after user authorization. Never reboots the phone,
changes service configuration, or restarts networking. No test app is launched.
"""
from pathlib import Path
import argparse, json, os, subprocess
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--expected-boot',required=True);p.add_argument('--expected-lipstick',required=True);p.add_argument('--restart-desktop',action='store_true');a=p.parse_args()
if not a.restart_desktop:raise SystemExit('Read the recovery transaction and obtain explicit user authorization before --restart-desktop')
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');os.environ['SSHPASS']=os.environ['SSHPASS']
config=dict(boot=a.expected_boot,lipstick=a.expected_lipstick)
body='CONFIG='+repr(config)+'\n'+r'''
from pathlib import Path
import os,pwd,subprocess,json,time
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('cts-desktop-recovery|')
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text()
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()==CONFIG['lipstick']
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:exe=os.readlink(proc/'exe')
 except OSError:continue
 assert not(exe.startswith('/home/art/releases/')and exe.endswith('/libexec/saildroid-host')),'Close owned test processes first'
u=pwd.getpwnam('defaultuser');env=dict(os.environ,HOME=u.pw_dir,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
kw=dict(env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid))
for name in ['sshd.socket','connman.service']:assert subprocess.check_output(['systemctl','is-active',name],text=True,timeout=5).strip()=='active'
watch=subprocess.Popen(['python3','-c',"import subprocess,time\nfor n in range(15):\n subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],timeout=5);time.sleep(4)"],start_new_session=True)
try:
 subprocess.run(['systemctl','--user','--no-block','restart','lipstick.service'],check=True,timeout=6,**kw)
 until=time.monotonic()+50;newpid=None;health=None
 while time.monotonic()<until:
  assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
  state=subprocess.run(['systemctl','--user','show','lipstick.service','-p','MainPID','-p','ActiveState','-p','SubState'],capture_output=True,text=True,timeout=5,**kw)
  values=dict(line.split('=',1)for line in state.stdout.splitlines()if '='in line)
  if values.get('ActiveState')=='active'and values.get('MainPID')not in[None,'0',CONFIG['lipstick']]:
   newpid=values['MainPID']
   health=subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],capture_output=True,text=True,timeout=5,**kw)
   if health.returncode==0:break
  time.sleep(.5)
 else:raise RuntimeError('Desktop restart did not reach fresh service and real Wayland sync within 50 seconds')
finally:
 subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True,timeout=5)
 blank_until=time.monotonic()+5
 while time.monotonic()<blank_until and Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()!='0':time.sleep(.1)
 watch.terminate();watch.wait(timeout=3)
assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert subprocess.check_output(['pidof','lipstick'],text=True).strip()==newpid
services={s:subprocess.check_output(['systemctl','is-active',s],text=True,timeout=5).strip()for s in['sshd.socket','connman.service']}
assert all(v=='active'for v in services.values())
assert Path('/home/art/api29-root').resolve()==Path('/home/art/releases/api29-r112-native-candidate')
print(json.dumps(dict(status='PASS',operation='single-user-lipstick-service-restart',boot=CONFIG['boot'],boot_unchanged=True,old_lipstick=CONFIG['lipstick'],lipstick=newpid,wayland_sync=health.stdout.strip(),services=services,brightness=0,daily='r112'),indent=2))
'''
subprocess.run(['bash',str(repo/'scripts/devlock.sh'),'acquire','0','cts-desktop-recovery'],check=True,timeout=15)
try:
 r=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input=body.encode(),capture_output=True,timeout=70)
 (a.evidence/'desktop-recovery-output.log').write_bytes(r.stdout+r.stderr)
 r.check_returncode();value=json.loads(r.stdout);(a.evidence/'desktop-recovery.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
finally:subprocess.run(['bash',str(repo/'scripts/devlock.sh'),'release','cts-desktop-recovery'],check=True,timeout=15)
