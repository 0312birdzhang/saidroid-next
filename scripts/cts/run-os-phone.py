from pathlib import Path
import os,subprocess,pwd,time,json,hashlib
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('official-cts-diagnostic|')
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip();base=Path('/home/art/test')/LABEL
apk=base/'official.apk';assert hashlib.sha256(apk.read_bytes()).hexdigest()==SHA
u=pwd.getpwnam('defaultuser');pkg='org.example.saildroid.ctsharness';data=Path('/home/art/apps')/pkg/'data';files=data/'files';files.mkdir(exist_ok=True)
# BinderTest is a separate BLOCKED diagnostic: its helper-component setup
# exceeded the 120-second deadline in cts-os-r114-2. Never count it as passed.
classes=['BadParcelableExceptionTest', 'BundleTest', 'DeadObjectExceptionTest', 'LocaleListTest', 'MessageTest', 'ParcelFormatExceptionTest', 'ParcelTest', 'PatternMatcherTest', 'RemoteExceptionTest', 'VibrationEffectTest', 'WorkSourceTest', 'BuildVersionTest', 'BuildTest']
(files/'plan.json').write_text(json.dumps(dict(apk=str(apk),classes=['android.os.cts.'+x for x in classes])))
for path in [base,apk,files,files/'plan.json']:os.chown(path,u.pw_uid,u.pw_gid)
result=files/'result.json';result.unlink(missing_ok=True)
env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket');kw=dict(env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid))
host='/home/art/releases/api29-r114-native-candidate/libexec/saildroid-app';record=None
watch=subprocess.Popen(['python3','-c',"import time,subprocess;time.sleep(135);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"],start_new_session=True)
try:
 subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True,timeout=5)
 with(base/'entry.log').open('w')as f:p=subprocess.Popen([host,'--package',pkg,'--debug-log'],stdout=f,stderr=subprocess.STDOUT,**kw)
 end=time.monotonic()+120
 while time.monotonic()<end:
  state=Path('/run/user/100000/saildroid')/(pkg+'.json')
  if state.exists():record=json.loads(state.read_text())
  if result.exists():break
  if p.poll()is not None:raise RuntimeError('Diagnostic host exited before result')
  time.sleep(.2)
 else:raise TimeoutError('Official tests exceeded bounded diagnostic window')
 value=json.loads(result.read_text());(base/'result.json').write_text(json.dumps(value,indent=2)+'\n')
 print('OFFICIAL_JUNIT_DIAGNOSTIC='+json.dumps({k:v for k,v in value.items()if k!='classes'}),flush=True)
finally:
 if record and Path(record['log']).exists():(base/'runtime.log').write_bytes(Path(record['log']).read_bytes())
 subprocess.run([host,'--package',pkg,'--close'],capture_output=True,timeout=18,**kw)
 subprocess.run([host,'--broker','--close'],capture_output=True,timeout=18,**kw)
 subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],timeout=5)
 watch.terminate();watch.wait(timeout=3)
 assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0'
 assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and lip==subprocess.check_output(['pidof','lipstick'],text=True).strip()
 print('DEVICE_FINAL=OLED-off|boot-and-lipstick-unchanged',flush=True)
