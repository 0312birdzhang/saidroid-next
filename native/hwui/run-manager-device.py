"""Exercise the installed manager's real HWUI window without installing any APK."""
from pathlib import Path
import json,os,pwd,signal,subprocess,sys,time
label,release=sys.argv[1:3]
account=pwd.getpwnam('defaultuser');root=Path('/home/art/api29-root');old=root.resolve()
candidate=Path('/home/art/releases')/release;assert candidate.is_dir()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
env=dict(os.environ,HOME=account.pw_dir,USER=account.pw_name,LOGNAME=account.pw_name,
 XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',
 DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket',
 WAYLAND_DEBUG='1',SAILDROID_ANDROID_LOG_STDERR='1')
user=dict(user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid))
def health():subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],env=env,check=True,timeout=5,**user)
def replace(target):
 p=Path('/home/art/.hwui-manager-root');assert not p.exists();p.symlink_to(target);os.replace(p,root)
watch=subprocess.Popen(['/bin/sh','-c','sleep 40; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
record=None;launched=False;supervisor=None
try:
 health();replace(candidate)
 subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
 supervisor=subprocess.Popen(['/home/art/bin/saildroid-open','--manager'],env=env,start_new_session=True,**user);launched=True
 deadline=time.monotonic()+20
 while time.monotonic()<deadline:
  state=Path('/run/user/100000/saildroid/org.saildroid.manager.json')
  if state.exists():
   candidate_record=json.loads(state.read_text())
   if candidate_record.get('supervisor_pid')!=supervisor.pid or candidate_record.get('boot')!=boot:
    time.sleep(.1);continue
   record=candidate_record
   text=Path(record['log']).read_text(errors='replace')
   if 'SDWINDOW_SESSION=drawn|' in text and 'SDHWUI=gpu_swap|' in text:break
   assert record.get('state')!='exited',(record,text[-1500:])
  time.sleep(.1)
 else:raise TimeoutError('Manager HWUI did not draw')
 assert 'renderer=Adreno (TM) 615' in text
 assert '.create_pool(' not in text
 assert 'SDRUNTIME=failed' not in text and 'Fatal glibc error' not in text
 subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True,timeout=4)
 subprocess.run(['/home/art/bin/saildroid-open','--manager'],env=env,check=True,timeout=8,**user)
 time.sleep(1)
 subprocess.run(['python3','/home/art/bin/sdtool.py','shot',label],check=True,timeout=10)
 print('HWUI_MANAGER=drawn|gpu=Adreno|private_installation=true|cpu_readback=0')
finally:
 try:
  if launched:
   subprocess.run(['/home/art/bin/saildroid-open','--manager','--close'],env=env,check=True,timeout=15,**user)
   deadline=time.monotonic()+6
   while time.monotonic()<deadline:
    final=json.loads(Path('/run/user/100000/saildroid/org.saildroid.manager.json').read_text())
    if final.get('state')=='exited':break
    time.sleep(.1)
  if supervisor is not None:
   supervisor.wait(timeout=8);assert supervisor.returncode==0,supervisor.returncode
  if record:Path('/home/art/test/'+label+'.log').write_bytes(Path(record['log']).read_bytes())
 finally:
  replace(old);subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
  deadline=time.monotonic()+4
  while time.monotonic()<deadline and Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()!='0':time.sleep(.1)
  try:os.killpg(watch.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  brightness=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip();print('FINAL_BRIGHTNESS='+brightness);assert brightness=='0'
  assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  assert lip==subprocess.check_output(['pidof','lipstick'],text=True).strip();health()
 if record:assert final.get('state')=='exited' and final.get('exit_code')==0,final
