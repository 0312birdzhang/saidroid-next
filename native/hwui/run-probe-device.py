"""Bounded, ordinary-user HWUI gate. Run via VM SSH while holding devlock."""
from pathlib import Path
import os,sys,json,pwd,subprocess,resource,ctypes,time,signal
label=sys.argv[1];probe_class='HwuiWindowProbe';assert label.replace('-','').isalnum()
root=Path('/home/art/releases')/sys.argv[2];assert root.is_dir()
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
account=pwd.getpwnam('defaultuser');manifest=json.loads((root/'runtime.json').read_text())
watch=subprocess.Popen(['/bin/sh','-c','sleep 35; mcetool --blank-screen'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
proc=None
def compositor_health():
 env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0')
 subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],env=env,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),check=True,timeout=5)
try:
 compositor_health()
 subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True,timeout=4)
 env=dict(os.environ,HOME=account.pw_dir,USER=account.pw_name,LOGNAME=account.pw_name,
  XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',
  DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket',
  ANDROID_ROOT=str(root),ANDROID_DATA='/home/art/data',LD_LIBRARY_PATH='/home/art/lib',
  ICU_DATA=str(root/'usr/icu'),SD_BUILD_PROP=str(root/'build.prop'),
  BIONIC_TRANSLATION_CONFIG_DIR=str(root/'linker-config'),SAILDROID_STRICT_LINK='1',
  LD_PRELOAD=str(root/'lib/libsdhost29.so')+':'+str(root/'lib/libdl_bio.so.0')+':libresolv.so.2',
  EXTERNAL_STORAGE='/home/art/data/shared',SAILDROID_HWUI='1',EGL_PLATFORM='wayland',
  HYBRIS_EGLPLATFORM='wayland',SAILDROID_ANDROID_LOG_STDERR='1',WAYLAND_DEBUG='1')
 if (root/'lib/libpthread_bio.so.0').exists():env['LD_PRELOAD']=str(root/'lib/libpthread_bio.so.0')+':'+env['LD_PRELOAD']
 command=['/home/art/bin/dalvikvm','-Xnoimage-dex2oat','-Xbootclasspath:'+':'.join(str(root/p) for p in manifest['boot_jars']),
 '-Djava.library.path='+str(root/'android-libs')+':/home/art/lib',
 '-Dsaidroid.bridge.library='+str(root/'lib/libsdbridge.so'),'-Dsaidroid.window.library='+str(root/'lib/libsdwindow.so'),
 '-Dsaidroid.ime.library='+str(root/'lib/libsdmaliit.so'),'-Dsaidroid.native.runtime='+str(root/'android-libs'),
 '-Dsaidroid.package=org.saildroid.manager','-Dsaidroid.apk='+str(root/'share/manager.apk'),
 '-Dsaidroid.native='+str(root/'empty-libs'),'-Dsaidroid.data=/home/art/data/manager',
 '-cp',str(root/'lib/runtime.jar')+':'+'/home/art/test/hwui-standalone-probe.jar',probe_class]
 resource.setrlimit(resource.RLIMIT_NICE,(28,28))
 def restrict():ctypes.CDLL(None).prctl(38,1,0,0,0)
 log=Path('/home/art/test')/(label+'.log')
 with log.open('wb') as stream:
  proc=subprocess.Popen(command,env=env,user=account.pw_uid,group=account.pw_gid,
   extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),preexec_fn=restrict,
   stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  shot=False;deadline=time.monotonic()+23
  while proc.poll() is None and time.monotonic()<deadline:
   text=log.read_text(errors='replace')
   if not shot and 'SDHWUI_PROBE=rendered|' in text:
    subprocess.run(['python3','/home/art/bin/sdtool.py','shot',label],check=True,timeout=12);shot=True
   time.sleep(.15)
  if proc.poll() is None:raise TimeoutError('HWUI probe exceeded bounded window')
 text=log.read_text(errors='replace')
 print('HWUI_EXIT='+str(proc.returncode))
 for line in text.splitlines():
  if any(s in line for s in ['SDEGL14','SDHWUI','FATAL','ERROR','Exception','Fatal','failed','not linked','eglInitialize','renderer=']):print(line)
 assert proc.returncode==0,'HWUI process failed'
 assert 'SDHWUI_PROBE=rendered|frames=12' in text
 assert 'SDHWUI=gpu_swap|' in text and 'success=1|renderer=Adreno' in text
 assert 'SDHWUI=unexpected_android_dequeue' not in text
 assert 'wl_shm@' not in text or '.create_pool(' not in text, 'software buffer allocation in HWUI path'
 assert 'android_wlegl' in text and '.attach(' in text,'GPU buffer presentation missing'
 assert shot,'No screenshot of the completed GPU scene'
 print('HWUI_NATIVE_WINDOW=ready|frames=12|gpu=Adreno|software_shm_pools=0|cpu_readback=0')
finally:
 if proc is not None and proc.poll() is None:
  os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=2)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 subprocess.run(['mcetool','--blank-screen'],check=True,timeout=4)
 try:os.killpg(watch.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 assert boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert lip==subprocess.check_output(['pidof','lipstick'],text=True).strip()
 deadline=time.monotonic()+4
 while time.monotonic()<deadline and Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()!='0':time.sleep(.1)
 brightness=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()
 print('FINAL_BRIGHTNESS='+brightness);assert brightness=='0'
 compositor_health()
