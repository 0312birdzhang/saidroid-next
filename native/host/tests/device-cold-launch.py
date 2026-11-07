"""One real drawer icon cold launch through the native host; bounded OLED."""
from pathlib import Path
import os,pwd,subprocess,time,json,signal,importlib.util,sys,types,hashlib
label=sys.argv[1];assert label.replace('-','').isalnum();tools=Path('/home/art/test/r86-ui-tools');sys.path.insert(0,str(tools));spec=importlib.util.spec_from_file_location('matrix',tools/'integration-matrix.py');matrix=importlib.util.module_from_spec(spec);spec.loader.exec_module(matrix)
u=pwd.getpwnam('defaultuser');env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket');user=dict(user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid));pkg='com.tencent.mobileqq';rt=Path('/run/user/100000/saildroid');root=Path('/home/art/api29-root').resolve();assert str(root)==os.environ.get('SAILDROID_EXPECT_COMPONENT','/home/art/releases/api29-r95-native-gate');host=root/'libexec/saildroid-app';boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
out=Path('/home/art/test')/label;out.mkdir(exist_ok=False);m=matrix.Matrix(types.SimpleNamespace(label=label));result=dict(root=str(root),boot=boot,lipstick=lip,tools_sha256=hashlib.sha256((tools/'integration-matrix.py').read_bytes()).hexdigest(),screens=[],phases={},top_history=[]);record=None;watch=None

def read(pkg):
 try:return json.loads((rt/(pkg+'.json')).read_text())
 except (OSError,ValueError):return {}
def alive(r):
 try:
  raw=Path('/proc/'+str(r['pid'])+'/stat').read_text();parts=raw[raw.rfind(') ')+2:].split();return int(parts[19])==r['start_ticks'] and parts[0]not in ['Z','X'] and r['boot']==boot
 except:return False
def shot(name):
 p=m.shot_dir/(name+'.png');matrix.run(['gdbus','call','--session','--dest','org.nemomobile.lipstick','--object-path','/org/nemomobile/lipstick/screenshot','--method','org.nemomobile.lipstick.saveScreenshot',str(p)],timeout=5)
 end=time.monotonic()+1.5;size=-1
 while time.monotonic()<end:
  if p.exists():
   n=p.stat().st_size
   if n==size and n>20000:break
   size=n
  time.sleep(.04)
 item=dict(path=str(p),bytes=p.stat().st_size if p.exists()else 0,t=round(time.monotonic()-start,3))
 if p.exists() and item['bytes']>0:
  w,h,rows=matrix.sd_covers.png_rows(p);colours=set()
  for y in range(300,h-200,40):
   for x in range(100,w-100,40):
    r,g,b,_=matrix.sd_covers.png_px(rows,x,y);colours.add((r//24,g//24,b//24))
  item['content_colours']=len(colours)
  if record and matrix.top()==record['pid']:assert len(colours)>1,'Flat startup/transition frame'
 result['screens'].append(item);return p

def close(pkg):
 args=['--broker']if pkg=='org.saildroid.binder'else['--package',pkg]
 r=read(pkg)
 if r.get('component')==str(root) and alive(r):
  done=subprocess.run([str(host)]+args+['--close'],env=env,timeout=18,capture_output=True,text=True,**user);print('CLOSE',pkg,done.returncode,done.stderr.strip(),flush=True)
  assert done.returncode==0
  assert not alive(r)
try:
 for p in rt.glob('*.json'):
  r=json.loads(p.read_text());assert not alive(r),'Cold launch precondition: live '+p.name
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:assert (proc/'exe').resolve()!=root/'libexec/saildroid-host','Native manager was already warm'
  except FileNotFoundError:pass
 watch=subprocess.Popen(['python3','-c',"import time,subprocess;time.sleep(60);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 subprocess.run(['mcetool','--set-never-blank=disabled','--unblank-screen','--set-tklock-mode=unlocked','--set-blank-timeout=35'],check=True,timeout=5)
 drawer=matrix.open_drawer(m,'native-drawer',attempts=3);watch.terminate();watch.wait(timeout=3);watch=subprocess.Popen(['python3','-c',"import time,subprocess;time.sleep(42);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True);subprocess.run(['mcetool','--unblank-screen','--set-blank-timeout=40'],check=True,timeout=5);before=read(pkg);print('PHYSICAL_ICON_TAP',drawer['icon'],flush=True);start=time.monotonic();wall=time.time();print(matrix.tap(drawer['icon']['cx'],drawer['icon']['cy']),flush=True)
 lastshot=-1;foreground_seen=False;ready=False
 while time.monotonic()-start<36:
  elapsed=time.monotonic()-start;r=read(pkg)
  if r.get('launch_id')!=before.get('launch_id') and r.get('component')==str(root):
   record=r;assert alive(r),'Native app ended during startup';text=Path(r['log']).read_text(errors='replace').replace('\x00','')
   for marker in ['SDHOST=registered','SDHOST=startup_mapped','SDHOST=art_bound','SDHOST=java_window_bound','SDHWUI=first_app_frame_presented','SDWINDOW_SESSION=drawn|title=com.tencent.mobileqq/com.tencent.mobileqq.activity.LoginActivity']:
    if marker in text and marker not in result['phases']:result['phases'][marker]=round(elapsed,3);print('PHASE',marker,round(elapsed,3),flush=True)
   pid=matrix.top();result['top_history'].append(dict(t=round(elapsed,3),pid=pid));assert pid in [0,r['pid']],'Unexpected foreground PID'
   if pid==r['pid']:foreground_seen=True
   elif foreground_seen:raise AssertionError('Topmost PID lost after native startup mapping')
   ready='SDWINDOW_SESSION=drawn|title=com.tencent.mobileqq/com.tencent.mobileqq.activity.LoginActivity'in result['phases']
  interval=.35 if elapsed<3 else 1
  if elapsed-lastshot>=interval:shot('native-start-%02d'%len(result['screens']));lastshot=time.monotonic()-start
  if ready:shot('native-login-ready');break
  time.sleep(.04)
 assert ready,'Native QQ did not reach real LoginActivity'
 text=Path(record['log']).read_text(errors='replace');assert 'same_pid=true'in text and 'reused=1'in text and 'icon=1|success=1'in text
 assert record['pid']==read(pkg)['pid'] and record['start_ticks']==read(pkg)['start_ticks']
 assert read(pkg).get('first_frame_seen') is True
 result['record']=record;result['status']='PASS';print('NATIVE_COLD_LAUNCH=PASS|entry=physical-icon|same_pid=true|early_window=true|login=true',flush=True)
finally:
 if record:
  (out/'qq.log').write_bytes(Path(record['log']).read_bytes());result['final_record']=read(pkg)
 cleanup_errors=[]
 for name in [pkg,'org.saildroid.binder']:
  try:close(name)
  except Exception as failure:cleanup_errors.append(str(failure));print('CLEANUP_ERROR',name,str(failure),flush=True)
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   if (proc/'exe').resolve()==root/'libexec/saildroid-host' and b'--session'in(proc/'cmdline').read_bytes():os.kill(int(proc.name),signal.SIGTERM)
  except (OSError,ValueError):pass
 subprocess.run(['mcetool','--set-never-blank=disabled','--set-blank-timeout=8','--blank-screen'],timeout=5)
 for _ in range(50):
  if Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0':break
  time.sleep(.1)
 if watch is not None:watch.terminate();watch.wait(timeout=3)
 result['brightness']=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip();result['final_boot']=Path('/proc/sys/kernel/random/boot_id').read_text().strip();result['final_lipstick']=subprocess.check_output(['pidof','lipstick'],text=True).strip();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('FINAL_BRIGHTNESS',result['brightness'],flush=True)
 assert not cleanup_errors,cleanup_errors
 assert result['brightness']=='0' and result['final_boot']==boot and result['final_lipstick']==lip
