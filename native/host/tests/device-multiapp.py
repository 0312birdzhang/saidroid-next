"""Native per-app hosts: overlapping real icon launches, dedup, cards, close."""
from pathlib import Path
import os,pwd,subprocess,time,json,signal,importlib.util,sys,types,hashlib
label=sys.argv[1];assert label.replace('-','').isalnum();tools=Path('/home/art/test/r86-ui-tools');sys.path.insert(0,str(tools));spec=importlib.util.spec_from_file_location('matrix',tools/'integration-matrix.py');matrix=importlib.util.module_from_spec(spec);spec.loader.exec_module(matrix)
u=pwd.getpwnam('defaultuser');env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket');user=dict(user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid));qq='com.tencent.mobileqq';manager='org.saildroid.manager';rt=Path('/run/user/100000/saildroid');root=Path('/home/art/api29-root').resolve();assert str(root)==os.environ.get('SAILDROID_EXPECT_COMPONENT','/home/art/releases/api29-r95-native-gate');host=root/'libexec/saildroid-app';boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip();out=Path('/home/art/test')/label;out.mkdir(exist_ok=False);m=matrix.Matrix(types.SimpleNamespace(label=label));result=dict(root=str(root),boot=boot,lipstick=lip,events=[],screens=[]);watch=None;start=time.monotonic()
def read(pkg):
 try:return json.loads((rt/(pkg+'.json')).read_text())
 except (OSError,ValueError):return {}
def alive(r):
 try:
  raw=Path('/proc/'+str(r['pid'])+'/stat').read_text();parts=raw[raw.rfind(') ')+2:].split();return int(parts[19])==r['start_ticks'] and parts[0]not in ['Z','X'] and r['boot']==boot
 except:return False
def event(name,**values):result['events'].append(dict(event=name,t=round(time.monotonic()-start,3),**values));print('EVENT',result['events'][-1],flush=True)
def text(pkg):
 r=read(pkg);return Path(r['log']).read_text(errors='replace').replace('\x00','') if r.get('log') and Path(r['log']).exists() else ''
def wait(check,seconds,why):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  value=check()
  if value:return value
  time.sleep(.08)
 raise AssertionError('Deadline: '+why)
def reset_watch(seconds=60):
 global watch
 if watch is not None:watch.terminate();watch.wait(timeout=3)
 watch=subprocess.Popen(['python3','-c',"import time,subprocess;time.sleep(%d);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"%seconds],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 subprocess.run(['mcetool','--set-never-blank=disabled','--unblank-screen','--set-tklock-mode=unlocked','--set-blank-timeout=50'],check=True,timeout=5)
def shot(name):
 p=matrix.screenshot(name,m.shot_dir);result['screens'].append(str(p));return p
def tap_icon(coords,name):event('physical_icon_tap',package=name,coords=coords);print(matrix.tap(*coords),flush=True)
def drawer_fast():
 matrix.swipe(540,2159,540,600,160,10);time.sleep(.45)
def close(pkg):
 r=read(pkg)
 if r.get('component')==str(root)and alive(r):
  args=['--broker']if pkg=='org.saildroid.binder'else['--manager']if pkg==manager else['--package',pkg]
  done=subprocess.run([str(host)]+args+['--close'],env=env,timeout=18,capture_output=True,text=True,**user);assert done.returncode==0,done.stderr;wait(lambda:not alive(r),3,'close exit');event('closed',package=pkg,launch_id=r['launch_id'])
try:
 for pkg in [qq,manager,'org.saildroid.binder']:assert not alive(read(pkg)),'Precondition live '+pkg
 if len(sys.argv)>2 and sys.argv[2]in ['cards-only','close-only']:
  previous=json.loads(Path('/home/art/test/native-r91-multiapp-card/result.json').read_text());assert previous['root']==str(root)and previous['boot']==boot
  icons=next(e for e in previous['events']if e['event']=='drawer_icons_verified');qcoords=tuple(icons['qq']);mcoords=tuple(icons['manager'])
  reset_watch(55);start=time.monotonic()
  with (out/'native-entry.log').open('w')as log:
   subprocess.Popen([str(host),'--package',qq],env=env,stdout=log,stderr=subprocess.STDOUT,**user)
   q0=wait(lambda:read(qq)if alive(read(qq))and read(qq).get('component')==str(root)else None,6,'QQ native host')
   subprocess.Popen([str(host),'--manager'],env=env,stdout=log,stderr=subprocess.STDOUT,**user)
   m0=wait(lambda:read(manager)if alive(read(manager))and read(manager).get('component')==str(root)else None,6,'Manager native host')
  wait(lambda:read(manager).get('first_frame_seen')and matrix.top()==m0['pid'],25,'Manager real frame')
  wait(lambda:'SDRUNTIME=application_ready'in text(qq),20,'QQ real application')
  event('focused_cards_fixture',qq_pid=q0['pid'],manager_pid=m0['pid'],entry='native-executable')
 else:
  reset_watch(75)
  drawer=matrix.open_drawer(m,'multi-drawer',attempts=3);qcoords=(drawer['icon']['cx'],drawer['icon']['cy']);hit=matrix.sd_covers.find_icon_center(drawer['path'],root/'share/icons/saildroid.png');assert hit,'Manager icon not in the same real drawer frame';mcoords=tuple(hit[:2]);event('drawer_icons_verified',qq=qcoords,manager=mcoords)
  reset_watch(65);start=time.monotonic();tap_icon(qcoords,qq)
  q0=wait(lambda:read(qq)if read(qq).get('component')==str(root)and alive(read(qq))and 'SDHOST=startup_mapped'in text(qq)else None,8,'QQ early window');event('qq_early_window',pid=q0['pid'],launch_id=q0['launch_id'])
  assert not read(qq).get('first_frame_seen'),'QQ finished before overlap test'
  drawer_fast();tap_icon(mcoords,manager)
  m0=wait(lambda:read(manager)if read(manager).get('component')==str(root)and alive(read(manager))and 'SDHOST=startup_mapped'in text(manager)else None,8,'Manager early window');event('manager_early_window',pid=m0['pid'],launch_id=m0['launch_id'])
  assert q0['pid']!=m0['pid'] and q0['launch_id']!=m0['launch_id']
  wait(lambda:read(manager).get('first_frame_seen') and matrix.top()==m0['pid'],25,'latest manager intent foreground and frame');shot('native-multi-manager');event('latest_intent_foreground',pid=m0['pid'])
  wait(lambda:'SDRUNTIME=application_ready'in text(qq),15,'QQ initialized independently');assert alive(q0)and alive(m0)
  # Repeating the same real Manager icon must keep exactly its old generation.
  drawer_fast();tap_icon(mcoords,manager);wait(lambda:matrix.top()==m0['pid'],5,'repeat manager foreground');assert read(manager)['launch_id']==m0['launch_id'];event('repeat_icon_dedup',package=manager,pid=m0['pid'])
  # Both hosts exist independently. Return to QQ via its real icon and require
  # a real LoginActivity frame, then show both Home cards.
  drawer_fast();tap_icon(qcoords,qq);wait(lambda:matrix.top()==q0['pid'],6,'QQ activation');wait(lambda:'SDWINDOW_SESSION=drawn|title=com.tencent.mobileqq/com.tencent.mobileqq.activity.LoginActivity'in text(qq),16,'QQ real login draw');shot('native-multi-qq');assert read(qq)['launch_id']==q0['launch_id'];event('qq_foreground_same_host',pid=q0['pid'])
 if len(sys.argv)<=2 or sys.argv[2]!='close-only':
  matrix.BACKGROUND_SWIPE();wait(lambda:matrix.top()==0,5,'Home background');reset_watch(60);time.sleep(1.3);home=shot('native-multi-home')
  qicon=Path(json.loads((Path('/home/art/apps')/qq/'record.json').read_text())['icon'])
  def card(frame,icon):
   hit=matrix.sd_covers.find_icon(frame,icon,sizes=(64,72,80,88,96));event('card_locator',icon=str(icon),match=hit);assert hit,'Native app card location unavailable';return hit
  qc=card(home,qicon);mc=card(home,root/'share/icons/saildroid.png');assert abs(qc['cx']-mc['cx'])+abs(qc['cy']-mc['cy'])>100,'Cards overlap';event('home_cards_located',qq=qc,manager=mc)
  # Tap the actual captured Home card to prove its PID mapping.
  event('physical_card_tap',package=qq,coords=(qc['cx'],qc['cy']));matrix.tap(qc['cx'],qc['cy']);wait(lambda:matrix.top()==q0['pid'],5,'QQ card activation');assert read(qq)['launch_id']==q0['launch_id'];event('qq_card_pid_verified',pid=q0['pid'])
  matrix.BACKGROUND_SWIPE();wait(lambda:matrix.top()==0,5,'Home again');time.sleep(1.3);home=shot('native-multi-home-after-qq');mc=card(home,root/'share/icons/saildroid.png');event('physical_card_tap',package=manager,coords=(mc['cx'],mc['cy']));matrix.tap(mc['cx'],mc['cy']);wait(lambda:matrix.top()==m0['pid'],5,'Manager card activation');event('manager_card_pid_verified',pid=m0['pid'])
 reset_watch(30);time.sleep(.9);shot('native-manager-before-close')
 # Close by a real top edge downward gesture, keeping QQ/Binder alive.
 event('physical_close_swipe',package=manager);matrix.swipe(20,1,20,1700,420,24);wait(lambda:not alive(m0),8,'Manager gesture close');assert alive(q0)and alive(read('org.saildroid.binder')),'Unrelated host or Broker ended';event('manager_closed_scope_preserved')
 # Relaunch the real Manager icon with a new generation and a new pid identity.
 drawer_fast();tap_icon(mcoords,manager);m1=wait(lambda:read(manager)if alive(read(manager))and read(manager).get('launch_id')!=m0['launch_id']else None,6,'Manager new generation');wait(lambda:read(manager).get('first_frame_seen')and matrix.top()==m1['pid'],10,'Manager relaunch frame');assert (m1['pid'],m1['start_ticks'])!=(m0['pid'],m0['start_ticks']);event('manager_relaunch',pid=m1['pid'],launch_id=m1['launch_id']);shot('native-manager-relaunch')
 result['status']='PASS';result['mode']=sys.argv[2]if len(sys.argv)>2 else'full';print(('NATIVE_CLOSE_LIFECYCLE=PASS|physical-close=true|relaunch=true'if result['mode']=='close-only'else'NATIVE_CARD_LIFECYCLE=PASS|cards=true|physical-close=true|relaunch=true'if result['mode']=='cards-only'else'NATIVE_MULTIAPP=PASS|overlap=true|dedup=true|cards=true|physical-close=true|relaunch=true'),flush=True)
finally:
 for name in [qq,manager,'org.saildroid.binder']:
  r=read(name)
  if r.get('component')==str(root)and r.get('log')and Path(r['log']).exists():(out/(name+'.log')).write_bytes(Path(r['log']).read_bytes())
 cleanup_errors=[]
 for name in [qq,manager,'org.saildroid.binder']:
  try:close(name)
  except Exception as failure:cleanup_errors.append(str(failure));print('CLEANUP_ERROR',name,str(failure),flush=True)
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   if(proc/'exe').resolve()==root/'libexec/saildroid-host'and b'--session'in(proc/'cmdline').read_bytes():os.kill(int(proc.name),signal.SIGTERM)
  except(OSError,ValueError):pass
 subprocess.run(['mcetool','--set-never-blank=disabled','--set-blank-timeout=8','--blank-screen'],timeout=5)
 for _ in range(50):
  if Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0':break
  time.sleep(.1)
 if watch is not None:watch.terminate();watch.wait(timeout=3)
 result['brightness']=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('FINAL_BRIGHTNESS',result['brightness'],flush=True)
 assert not cleanup_errors,cleanup_errors
 assert result['brightness']=='0'and boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and lip==subprocess.check_output(['pidof','lipstick'],text=True).strip()
