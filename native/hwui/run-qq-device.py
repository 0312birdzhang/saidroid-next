from pathlib import Path
import os,sys,json,subprocess,time,signal,pwd
label=sys.argv[1];pkg='com.tencent.mobileqq';tool='/home/art/bin/sdtool.py'
account=pwd.getpwnam('defaultuser')
root=Path('/home/art/api29-root');old=root.resolve();candidate=Path('/home/art/releases')/sys.argv[2];assert candidate.is_dir()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
watch=subprocess.Popen(['/bin/sh','-c','sleep 140; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
record=None;visible_watch=None;launch_watch=None
def replace_root(target):
 link=Path('/home/art/.hwui-test-root');assert not link.exists();link.symlink_to(target);os.replace(link,root)
def wait_marker(marker,timeout=10):
 deadline=time.monotonic()+timeout;diagnosed=False
 while time.monotonic()<deadline:
  text=Path(record['log']).read_text(errors='replace')
  if marker in text:return text
  if 'SDRUNTIME=failed' in text:raise AssertionError(text[-3500:])
  if not diagnosed and time.monotonic()>deadline-timeout+12:
   env=dict(os.environ,HOME=account.pw_dir,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
   subprocess.run(['/home/art/bin/saildroid-open','--package',pkg,'--dump-threads'],env=env,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),timeout=5)
   diagnosed=True
  time.sleep(.1)
 raise AssertionError('Missing marker '+marker+'\n'+text[-3500:])
def compositor_health():
 env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0')
 subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],env=env,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),check=True,timeout=5)
try:
 compositor_health()
 replace_root(candidate)
 subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True,timeout=4)
 launch_watch=subprocess.Popen(['/bin/sh','-c','sleep 12; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['python3',tool,'--package',pkg,'launch','--env','SAILDROID_DIAG_INPUT=1','--env','SAILDROID_ANDROID_LOG_STDERR=1','--env','WAYLAND_DEBUG=1','--wait','15'],check=True,timeout=22)
 record=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
 wait_marker('SDWINDOW=ready|',8)
 subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
 try:os.killpg(launch_watch.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 wait_marker('SDRUNTIME=activity_queued',90)
 wait_marker('SDHWUI=gpu_swap|',8)
 subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True,timeout=4)
 visible_watch=subprocess.Popen(['/bin/sh','-c','sleep 38; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 wait_marker('SDWINDOW_SESSION=drawn|title=com.tencent.mobileqq/com.tencent.mobileqq.activity.LoginActivity',30)
 env_user=dict(os.environ,HOME=account.pw_dir,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
 subprocess.run(['/home/art/bin/saildroid-open','--package',pkg],env=env_user,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),timeout=5)
 time.sleep(1.2)
 subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-before'],check=True,timeout=12)
 steps='tap 791 1900 60\nsleep 1300\ntap 1005 152 60\nsleep 1300\ntap 400 1803 60\n'
 subprocess.run(['/home/art/bin/sdinput','serve'],input=steps,text=True,check=True,timeout=12)
 wait_marker('QQBrowserActivity',8)
 wait_marker('"event":"load","status":2',22)
 wait_marker('SDWEBVIEW=draw|renderer=qt-wpe',5)
 time.sleep(2)
 subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-h5'],check=True,timeout=12)
 text=Path(record['log']).read_text(errors='replace')
 assert 'SDHWUI=gpu_swap|' in text and 'renderer=Adreno (TM) 615' in text
 assert 'SDRUNTIME=failed' not in text
 assert 'Fatal glibc error' not in text and 'Fatal signal' not in text
 maps=Path('/proc/'+str(record['pid'])+'/maps').read_text()
 if (candidate/'lib/libpthread_bio.so.0').exists():
  assert str(candidate/'lib/libpthread_bio.so.0') in maps
  assert '/home/art/lib/libpthread_bio.so.0' not in maps
 print('HWUI_QQ_START=ready|gpu=Adreno|webview_pixels=pending')
finally:
 close_result=subprocess.run(['python3',tool,'--package',pkg,'close'],timeout=15)
 if record:
  Path('/home/art/test/'+label+'.log').write_bytes(Path(record['log']).read_bytes())
 if record:
  exit_deadline=time.monotonic()+6
  while time.monotonic()<exit_deadline:
   final=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
   if final.get('state')=='exited':break
   time.sleep(.1)
  Path('/home/art/test/'+label+'.log').write_bytes(Path(record['log']).read_bytes())
 subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
 env=dict(os.environ,HOME=account.pw_dir,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
 subprocess.run(['/home/art/bin/saildroid-open','--broker','--close'],env=env,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),timeout=8)
 replace_root(old)
 deadline=time.monotonic()+4
 while time.monotonic()<deadline and Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()!='0':time.sleep(.1)
 if launch_watch is not None:
  try:os.killpg(launch_watch.pid,signal.SIGTERM)
  except ProcessLookupError:pass
 if visible_watch is not None:
  try:os.killpg(visible_watch.pid,signal.SIGTERM)
  except ProcessLookupError:pass
 try:os.killpg(watch.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 brightness=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip();print('FINAL_BRIGHTNESS='+brightness);assert brightness=='0'
 assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert lip==subprocess.check_output(['pidof','lipstick'],text=True).strip()
 compositor_health()

 if record:
  final=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
  assert final.get('state')=='exited' and final.get('exit_code')==0, ('lifecycle exit',final.get('state'),final.get('exit_code'))
