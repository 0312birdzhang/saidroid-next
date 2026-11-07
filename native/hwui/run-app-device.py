from pathlib import Path
import os,sys,json,subprocess,time,signal,pwd
label=sys.argv[1];pkg='org.example.saildroid.hwuiprobe';tool='/home/art/bin/sdtool.py'
account=pwd.getpwnam('defaultuser')
root=Path('/home/art/api29-root');old=root.resolve();candidate=Path('/home/art/releases')/sys.argv[2];assert candidate.is_dir()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
software=len(sys.argv)>3 and sys.argv[3]=='software'
expect=str(not software).lower()
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
 subprocess.run(['python3',tool,'--package',pkg,'launch','--env','SAILDROID_DIAG_INPUT=1','--env','SAILDROID_ANDROID_LOG_STDERR=1','--env','WAYLAND_DEBUG=1','--wait','15'],check=True,timeout=22)
 record=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
 wait_marker('SDHWUI_APP=draw|view_hardware='+expect+'|canvas_hardware='+expect,14)
 if not software:wait_marker('SDHWUI=gpu_swap|',8)
 subprocess.run(['mcetool','--unblank-screen','--set-tklock-mode=unlocked'],check=True,timeout=4)
 deadline=time.monotonic()+5
 while time.monotonic()<deadline and Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0':time.sleep(.05)
 wait_marker('SDWINDOW=seat_focus|active=true',5)
 time.sleep(.5)
 subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-before'],check=True,timeout=12)
 time.sleep(1)
 subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-settled'],check=True,timeout=12)
 subprocess.run(['/home/art/bin/sdinput','tap','500','1030','60'],check=True,timeout=5)
 wait_marker('SDHWUI_APP=click|count=1|view_hardware='+expect,5)
 time.sleep(.3)
 subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-after'],check=True,timeout=12)
 subprocess.run(['/home/art/bin/sdinput','tap','500','1280','60'],check=True,timeout=5)
 wait_marker('SDHWUI_APP=dialog_open',5)
 if not software:wait_marker('SDHWUI=egl_window_surface|id=2',5)
 time.sleep(.6)
 subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-dialog'],check=True,timeout=12)
 subprocess.run(['/home/art/bin/sdinput','tap','895','1215','60'],check=True,timeout=5)
 wait_marker('SDHWUI_APP=dialog_closed',5)
 time.sleep(.3)
 subprocess.run(['/home/art/bin/sdinput','tap','500','1030','60'],check=True,timeout=5)
 wait_marker('SDHWUI_APP=click|count=2|view_hardware='+expect,5)
 env_user=dict(os.environ,HOME=account.pw_dir,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
 def cpu_ticks():
  raw=Path('/proc/'+str(record['pid'])+'/stat').read_text();v=raw[raw.rfind(') ')+2:].split();return int(v[11])+int(v[12])
 for cycle in range(2):
  current=Path(record['log']).read_text(errors='replace');before_pause=current.count('SDACTIVITY=host_visibility|foreground=false')
  before_resume=current.count('SDACTIVITY=host_visibility|foreground=true')
  subprocess.run(['/home/art/bin/sdinput','swipe','1079','800','400','800','300','24'],check=True,timeout=5)
  deadline=time.monotonic()+4
  while time.monotonic()<deadline and Path(record['log']).read_text(errors='replace').count('SDACTIVITY=host_visibility|foreground=false')<=before_pause:time.sleep(.1)
  assert Path(record['log']).read_text(errors='replace').count('SDACTIVITY=host_visibility|foreground=false')>before_pause
  time.sleep(.4);ticks0=cpu_ticks();started=time.monotonic();time.sleep(2)
  idle_cpu=(cpu_ticks()-ticks0)/os.sysconf('SC_CLK_TCK')/(time.monotonic()-started)*100
  assert idle_cpu<8,('background CPU',idle_cpu)
  subprocess.run(['/home/art/bin/saildroid-open','--package',pkg],env=env_user,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),timeout=5)
  deadline=time.monotonic()+5
  while time.monotonic()<deadline and Path(record['log']).read_text(errors='replace').count('SDACTIVITY=host_visibility|foreground=true')<=before_resume:time.sleep(.1)
  assert Path(record['log']).read_text(errors='replace').count('SDACTIVITY=host_visibility|foreground=true')>before_resume
  # Check the resumed frame before a tap can force an otherwise missing redraw.
  time.sleep(.4)
  subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-resume'+str(cycle+1)],check=True,timeout=12)
  current_record=json.loads(Path('/run/user/100000/saildroid/'+pkg+'.json').read_text())
  assert current_record['pid']==record['pid'] and current_record['start_ticks']==record['start_ticks']
  subprocess.run(['/home/art/bin/sdinput','tap','500','1030','60'],check=True,timeout=5)
  wait_marker('SDHWUI_APP=click|count='+str(3+cycle)+'|view_hardware='+expect,5)
  print('HWUI_LIFECYCLE=returned|cycle='+str(cycle+1)+'|same_pid=true|background_cpu_percent='+str(round(idle_cpu,3)))
 time.sleep(.5)
 subprocess.run(['python3',tool,'--package',pkg,'shot',label+'-returned'],check=True,timeout=12)
 text=Path(record['log']).read_text(errors='replace')
 if software:
  assert 'SDHWUI=app_opt_out|selected=software-wayland' in text
 else:
  assert 'SDHWUI=gpu_swap|' in text and 'renderer=Adreno (TM) 615' in text
  assert 'wl_shm' not in text or '.create_pool(' not in text
 assert 'SDHWUI=unexpected_android_dequeue' not in text
 assert 'SDRUNTIME=failed' not in text
 print('ANDROID_RENDERER_APP=ready|hardware='+expect+'|click_count=4|dialog_open_close=true|cover_cycles=2')
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
