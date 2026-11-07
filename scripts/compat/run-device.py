from pathlib import Path
import os,sys,json,subprocess,time,signal,pwd
label=sys.argv[1];pkg='org.example.saildroid.compatprobe';tool='/home/art/bin/sdtool.py'
account=pwd.getpwnam('defaultuser')
root=Path('/home/art/api29-root');old=root.resolve();candidate=Path('/home/art/releases')/sys.argv[2];assert candidate.is_dir()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
watch=subprocess.Popen(['/bin/sh','-c','sleep 48; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
record=None
def replace_root(target):
 link=Path('/home/art/.hwui-test-root');assert not link.exists();link.symlink_to(target);os.replace(link,root)
def wait_marker(marker,timeout=10):
 deadline=time.monotonic()+timeout
 while time.monotonic()<deadline:
  text=Path(record['log']).read_text(errors='replace')
  if marker in text:return text
  if 'SDRUNTIME=failed' in text:raise AssertionError(text[-3500:])
  time.sleep(.1)
 raise AssertionError('Missing marker '+marker+'\n'+text[-3500:])
def compositor_health():
 env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0')
 subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],env=env,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),check=True,timeout=5)
try:
 compositor_health()
 replace_root(candidate)
 subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
 subprocess.run(['python3',tool,'--package',pkg,'launch','--env','SAILDROID_ANDROID_LOG_STDERR=1','--wait','15'],check=True,timeout=22)
 record=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
 text=wait_marker('SDCOMPAT=complete|',30)
 complete=[line for line in text.splitlines() if 'SDCOMPAT=complete|' in line][-1]
 print(complete)
 assert '|failed=0|' in complete, '\n'.join(line for line in text.splitlines() if 'SDCOMPAT=' in line)
 assert text.count('SDCOMPAT=pass|case=')==24
 wait_marker('SDHWUI=first_app_frame_presented|parent_mapped=true',8)
 assert 'SDRUNTIME=failed' not in text
 print('ANDROID_API29_CONTRACTS=ready|cases=24|signed_apk=true|screen_off=true')

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
 try:os.killpg(watch.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 brightness=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip();print('FINAL_BRIGHTNESS='+brightness);assert brightness=='0'
 assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert lip==subprocess.check_output(['pidof','lipstick'],text=True).strip()
 compositor_health()

 if record:
  final=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
  assert final.get('state')=='exited' and final.get('exit_code')==0, ('lifecycle exit',final.get('state'),final.get('exit_code'))
