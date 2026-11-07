"""Ordinary Android View: a real touch drives native script and navigation callbacks."""
from pathlib import Path
import os,pwd,subprocess,json,time,signal,sys
label=sys.argv[1];pkg='org.example.saildroid.webviewprobe';tool='/home/art/bin/sdtool.py'
a=pwd.getpwnam('defaultuser');env=dict(os.environ,HOME=a.pw_dir,USER=a.pw_name,LOGNAME=a.pw_name,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
user=dict(user=a.pw_uid,group=a.pw_gid,extra_groups=os.getgrouplist(a.pw_name,a.pw_gid))
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
watch=subprocess.Popen(['/bin/sh','-c','sleep 35; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
server=None;record=None
serverLog=Path('/home/art/test')/(label+'-requests.jsonl')
serverLog.touch(exist_ok=False);os.chown(serverLog,a.pw_uid,a.pw_gid)
def health():
 e=dict(env,WAYLAND_DISPLAY='../../display/wayland-0');subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],env=e,check=True,timeout=5,**user)
def wait(marker,timeout=15):
 deadline=time.monotonic()+timeout
 while time.monotonic()<deadline:
  text=Path(record['log']).read_text(errors='replace')
  if marker in text:return text
  if 'SDRUNTIME=failed' in text or 'SDVERIFY=error' in text:raise AssertionError(text[-3000:])
  time.sleep(.05)
 raise AssertionError('missing '+marker+'\n'+text[-2500:])
try:
 health();subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
 server=subprocess.Popen(['python3','/home/art/test/verification-server-r86.py',str(serverLog)],start_new_session=True,**user);time.sleep(.2);assert server.poll()is None
 subprocess.run(['python3',tool,'--package',pkg,'launch','--env','SAILDROID_ANDROID_LOG_STDERR=1','--wait','15'],check=True,timeout=22)
 record=json.loads((Path('/run/user/100000/saildroid')/(pkg+'.json')).read_text())
 wait('SDVERIFY=finished|path=/start');wait('SDVERIFY=cookies|android=true|server=true')
 text=wait('SDVERIFY=state|');states=[json.loads(json.loads(line.split('SDVERIFY=state|',1)[1]))for line in text.splitlines()if 'SDVERIFY=state|' in line];assert states[0]['hidden']=='undefined'
 assert 'SDWEBVIEW=placeholder|' not in text
 assert 'SDHWUI=first_app_frame_presented|parent_mapped=true' in text
 subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True,timeout=4)
 subprocess.run(['/home/art/bin/saildroid-open','--package',pkg],env=env,check=True,timeout=5,**user)
 wait('SDWEBVIEW=draw|renderer=qt-wpe');time.sleep(.7);subprocess.run(['python3',tool,'shot',label+'-before'],check=True,timeout=10)
 # Button occupies the central half-height area in a normal Android WebView.
 subprocess.run(['/home/art/bin/sdinput','tap','540','650','70'],check=True,timeout=5)
 wait('SDVERIFY=java_call|count=1');wait('SDVERIFY=prompt|handled=true');wait('SDVERIFY=navigation|scheme=testbridge');wait('SDVERIFY=finished|path=/next')
 wait('Native callback and redirect handled')
 time.sleep(.5);subprocess.run(['python3',tool,'shot',label+'-after'],check=True,timeout=10)
 requests=[json.loads(x)for x in serverLog.read_text().splitlines()]
 assert any(r['path']=='/start' and r['test_header']=='android-provider' and 'fromAndroid=one' in r['cookies'] and 'secondCookie=two' in r['cookies'] for r in requests),requests
 assert any(r['path']=='/next' for r in requests)
 print('ANDROID_VERIFICATION_FLOW=ready|physical_tap=true|annotated_java_bridge=true|prompt=true|custom_uri=true|http_redirect=true|cookies=true|headers=true|debug_placeholder=false')
finally:
 try:
  subprocess.run(['python3',tool,'--package',pkg,'close'],timeout=15)
  if record:
   deadline=time.monotonic()+6
   while time.monotonic()<deadline:
    final=json.loads((Path('/run/user/100000/saildroid')/(pkg+'.json')).read_text())
    if final.get('state')=='exited':break
    time.sleep(.1)
   Path('/home/art/test/'+label+'.log').write_bytes(Path(record['log']).read_bytes())
   assert final.get('state')=='exited' and final.get('exit_code')==0,final
 finally:
  if server is not None and server.poll()is None:os.killpg(server.pid,signal.SIGTERM);server.wait(timeout=4)
  subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
  deadline=time.monotonic()+4
  while time.monotonic()<deadline and Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()!='0':time.sleep(.1)
  try:os.killpg(watch.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0';print('FINAL_BRIGHTNESS=0')
  assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert lip==subprocess.check_output(['pidof','lipstick'],text=True).strip();health()
