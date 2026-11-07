from pathlib import Path
import os,json,subprocess,pwd,time,hashlib,base64,shutil,traceback
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot=='4fab5d11-f3fd-4a5f-8724-f20785e27485';lip=subprocess.check_output(['pidof','lipstick'],text=True).strip();assert lip=='9463';assert Path('/home/art/test/.device-lock/owner').read_text().startswith('cover307-fixture|')
root=Path(CFG['root']);pkg='org.example.saildroid.cover';app=Path('/home/art/apps')/pkg;assert not app.exists();base=Path('/home/art/test')/CFG['label'];base.mkdir(mode=0o700);u=pwd.getpwnam('defaultuser');env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket');kw=dict(env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid));record=None;child=None;watch=None;result=dict(passed=False,root=str(root),target_sdk=CFG['target_sdk'],expected=CFG['expected'],cycles=[])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();apk=base/'fixture.apk';apk.write_bytes(base64.b64decode(CFG['apk']));assert sha(apk)==CFG['sha256']
def alive():
 try:
  p=Path('/proc')/str(record['pid']);f=(p/'stat').read_text().rsplit(') ',1)[1].split();return f[0]not in ['Z','X']and int(f[19])==record['start_ticks']and record['boot']==boot and (p/'exe').resolve()==root/'libexec/saildroid-host'
 except (OSError,TypeError,KeyError):return False
def text():return Path(record['log']).read_text(errors='replace').replace(chr(0),'')if record else''
def wait(marker,count=1,timeout=10):
 until=time.monotonic()+timeout
 while time.monotonic()<until:
  if text().count(marker)>=count:return
  assert alive(),'Fixture process exited while waiting for '+marker
  time.sleep(.1)
 raise AssertionError('Missing '+marker+'; tail='+text()[-2000:])
def input(command):
 q=subprocess.run(['/home/art/bin/sdinput','serve'],input='sleep 1200\n'+command+'\n',capture_output=True,text=True,timeout=8);assert q.returncode==0,q.stderr
 result.setdefault('input_intents',[]).append(dict(command=command,output=q.stdout))
def capture(tag):
 folder=Path(u.pw_dir)/'Downloads/SailDroid-Screenshots'/CFG['label'];folder.mkdir(exist_ok=True);os.chown(folder,u.pw_uid,u.pw_gid);p=folder/(tag+'.png');assert not p.exists()
 q=subprocess.run(['gdbus','call','--session','--dest','org.nemomobile.lipstick','--object-path','/org/nemomobile/lipstick/screenshot','--method','org.nemomobile.lipstick.saveScreenshot',str(p)],capture_output=True,text=True,env=env,timeout=5);assert q.returncode==0,q.stderr;time.sleep(.35);assert p.read_bytes()[:8]==bytes.fromhex('89504e470d0a1a0a');shutil.copyfile(p,base/p.name)
def locate_card(tag,generation):
 import types,statistics
 helper=types.ModuleType('cover_png');exec(PNG_HELPER,helper.__dict__)
 w,h,rows=helper.png_rows(str(base/(tag+'.png')))
 matches=[]
 for x in range(100,w-70,50):
  colours=[[],[],[]]
  for y in range(160,min(810,h-100),20):
   r,g,blue,_=helper.png_px(rows,x,y)
   if r>245 and g<10 and blue<10:colours[0].append(y)
   if g>245 and r<10 and blue<10:colours[1].append(y)
   if blue>245 and r<10 and g<10:colours[2].append(y)
  if all(len(v)>=3 for v in colours):matches.append((x,[statistics.mean(v)for v in colours]))
 if not matches:return None
 means=[statistics.mean(v[1][c]for v in matches)for c in range(3)]
 order=sorted(range(3),key=lambda c:means[c]);expected=[0,1,2]if generation%2==0 else[2,0,1]
 assert order==expected,('Cover generation differs from app frame',order,expected)
 return dict(x=round(statistics.mean(v[0]for v in matches)),y=round(statistics.mean(means)),colour_y=means,order=order,matched_columns=len(matches))
try:
 assert blank_display()['ready'];app.mkdir();(app/'lib').mkdir();(app/'data/files').mkdir(parents=True);shutil.copyfile(apk,app/'app.apk');(app/'icon.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='));(app/'record.json').write_text(json.dumps(dict(package=pkg,apk=str(app/'app.apk'),native=str(app/'lib'),data=str(app/'data'),icon=str(app/'icon.png'),apkSha256=CFG['sha256'],debuggable=False)))
 for p in [app,*app.rglob('*')]:os.chown(p,u.pw_uid,u.pw_gid)
 watch=subprocess.Popen(['python3','-c',"import subprocess,time;time.sleep(110);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],timeout=5)"],start_new_session=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['mcetool','--set-never-blank=disabled','--unblank-screen','--set-tklock-mode=unlocked'],check=True,capture_output=True,timeout=5)
 with(base/'entry.log').open('ab',buffering=0)as stream:child=subprocess.Popen([str(root/'libexec/saildroid-app'),'--package',pkg],stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,**kw)
 until=time.monotonic()+45
 while time.monotonic()<until:
  state=Path('/run/user/100000/saildroid')/(pkg+'.json')
  if state.exists():
   v=json.loads(state.read_text())
   if v.get('pid')==child.pid and v.get('component')==str(root):record=v
  if record and 'COVER_PROBE=draw|generation=0|hardware=true'in text():break
  assert child.poll()is None,'Fixture exited before draw';time.sleep(.1)
 assert record and alive();wait('COVER_PROBE=draw|generation=0|hardware=true');result.update(pid=record['pid'],start_ticks=record['start_ticks']);time.sleep(.5);capture('foreground-0')
 for cycle in range(2):
  before=text();pause_before=before.count('SDACTIVITY=host_visibility|foreground=false');resume_before=before.count('SDACTIVITY=host_visibility|foreground=true');commit_before=before.count('SDCOVER=committed|')
  input('swipe 1079 800 400 800 300 24');wait('SDACTIVITY=host_visibility|foreground=false',pause_before+1);time.sleep(1.0);capture('cover-'+str(cycle));card=locate_card('cover-'+str(cycle),cycle);result.setdefault('card_pixels',[]).append(card);after=text();result['cycles'].append(dict(generation=cycle,physical_background=True,new_cover_snapshot=after.count('SDCOVER=snapshot|')>before.count('SDCOVER=snapshot|'),new_cover_commit=after.count('SDCOVER=committed|')>commit_before,same_pid=alive()))
  
  if CFG['expected']=='pass':
   assert card,'Controlled RGB card not found';input('tap '+str(card['x'])+' '+str(card['y']))
  else:
   subprocess.run([str(root/'libexec/saildroid-app'),'--package',pkg],capture_output=True,check=True,timeout=10,**kw)
  wait('SDACTIVITY=host_visibility|foreground=true',resume_before+1);time.sleep(.5);capture('resumed-'+str(cycle));assert alive()
  if cycle==0:input('tap 200 600');wait('COVER_PROBE=tap|generation=1');wait('COVER_PROBE=draw|generation=1|hardware=true');time.sleep(.3);capture('foreground-1')
 if CFG['expected']=='pass'and CFG['target_sdk']==34:
  input('tap 850 650');wait('COVER_PROBE=dialog-open');time.sleep(.3);capture('foreground-dialog')
  before=text();pause_before=before.count('SDACTIVITY=host_visibility|foreground=false');resume_before=before.count('SDACTIVITY=host_visibility|foreground=true')
  input('swipe 1079 800 400 800 300 24');wait('SDACTIVITY=host_visibility|foreground=false',pause_before+1);time.sleep(1);capture('cover-dialog')
  import types
  helper=types.ModuleType('cover_png');exec(PNG_HELPER,helper.__dict__);w,h,rows=helper.png_rows(str(base/'cover-dialog.png'));card=result['card_pixels'][-1];cyan=0
  for x in range(card['x']-100,card['x']+101,20):
   for y in range(card['y']-70,card['y']+71,20):
    r,g,blue,_=helper.png_px(rows,x,y)
    if r<10 and g>245 and blue>245:cyan+=1
  assert cyan>10,('Dialog pixels missing from cover',cyan)
  after=text();result['cycles'].append(dict(generation=1,dialog=True,cyan_samples=cyan,physical_background=True,new_cover_snapshot=after.count('SDCOVER=snapshot|')>before.count('SDCOVER=snapshot|'),new_cover_commit=after.count('SDCOVER=committed|')>before.count('SDCOVER=committed|'),same_pid=alive()))
  input('tap '+str(card['x'])+' '+str(card['y']));wait('SDACTIVITY=host_visibility|foreground=true',resume_before+1);time.sleep(.3);capture('resumed-dialog');input('tap 540 1080');wait('COVER_PROBE=dialog-closed')
 result['semantic_pass']=all(c['same_pid']and c['new_cover_snapshot']and c['new_cover_commit']for c in result['cycles']);result['passed']=result['semantic_pass']if CFG['expected']=='pass'else not result['semantic_pass'];result['actual_target_marker']='SDRUNTIME=sdk_policy|target='+str(CFG['target_sdk'])+'|source=parsed-apk-manifest'in text();assert result['actual_target_marker']
except BaseException as error:result['error']=repr(error);traceback.print_exc()
finally:
 if record:
  shutil.copyfile(record['log'],base/'runtime.log')
  if alive():q=subprocess.run([str(root/'libexec/saildroid-app'),'--package',pkg,'--close'],capture_output=True,timeout=18,**kw);result['close_code']=q.returncode
 if child:
  try:child.wait(timeout=6)
  except subprocess.TimeoutExpired:result['cleanup_process_alive']=True
 result['display_cleanup']=blank_display()
 if watch and result['display_cleanup']['ready']:watch.terminate();watch.wait(timeout=3)
 if record:shutil.copyfile(record['log'],base/'runtime.log')
 if not alive()and app.exists():assert json.loads((app/'record.json').read_text())['package']==pkg and sha(app/'app.apk')==CFG['sha256'];shutil.rmtree(app);result['fixture_removed']=True
 result['cleanup_safe']=result['display_cleanup']['ready']and not alive()and result.get('fixture_removed',False)and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and subprocess.check_output(['pidof','lipstick'],text=True).strip()==lip
 (base/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
assert result['passed']and result['cleanup_safe']
