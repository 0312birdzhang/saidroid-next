"""Targeted installer native API and existing-host APK request regression."""
from pathlib import Path
import subprocess,os,pwd,time,json,signal,hashlib,importlib.util,sys
label=sys.argv[1];out=Path('/home/art/test')/label;out.mkdir(exist_ok=False);root=Path('/home/art/api29-root').resolve();assert str(root)==os.environ.get('SAILDROID_EXPECT_COMPONENT','/home/art/releases/api29-r95-native-gate');host=root/'libexec/saildroid-app';rt=Path('/run/user/100000/saildroid');u=pwd.getpwnam('defaultuser');env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket');kw=dict(env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid));boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip();qq='com.tencent.mobileqq';manager='org.saildroid.manager';source=Path('/home/art/apps')/qq/'record.json';before_hash=hashlib.sha256(source.read_bytes()).hexdigest();watch=None;result=dict(root=str(root),boot=boot)
tools=Path('/home/art/test/r86-ui-tools');sys.path.insert(0,str(tools));spec=importlib.util.spec_from_file_location('matrix',tools/'integration-matrix.py');matrix=importlib.util.module_from_spec(spec);spec.loader.exec_module(matrix);shots=Path(u.pw_dir)/'Downloads/SailDroid-Screenshots'/label;shots.mkdir(exist_ok=False);os.chown(shots,u.pw_uid,u.pw_gid)
def read(name):
 try:return json.loads((rt/(name+'.json')).read_text())
 except:return {}
def alive(r):
 try:
  raw=Path('/proc/'+str(r['pid'])+'/stat').read_text();f=raw[raw.rfind(') ')+2:].split();return r['boot']==boot and int(f[19])==r['start_ticks'] and f[0]not in ['Z','X']
 except:return False
def text(name):
 r=read(name);return Path(r['log']).read_text(errors='replace').replace('\x00','') if r.get('log')and Path(r['log']).exists()else ''
def wait(check,seconds,message):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  value=check()
  if value:return value
  time.sleep(.08)
 raise AssertionError(message)
def call(args,seconds=18):return subprocess.run([str(host)]+args,capture_output=True,text=True,timeout=seconds,**kw)
def close(name):
 r=read(name)
 if alive(r):
  args=['--broker']if name=='org.saildroid.binder'else['--manager']if name==manager else['--package',name]
  x=call(args+['--close']);assert x.returncode==0,x.stderr;wait(lambda:not alive(r),3,'close exit')
try:
 assert not any(alive(read(n))for n in [qq,manager,'org.saildroid.binder'])
 watch=subprocess.Popen(['python3','-c',"import time,subprocess;time.sleep(65);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL,start_new_session=True)
 subprocess.run(['mcetool','--set-never-blank=disabled','--set-blank-timeout=60','--unblank-screen','--set-tklock-mode=unlocked'],check=True,timeout=5)
 with(out/'entry.log').open('w')as log:subprocess.Popen([str(host),'--manager'],stdout=log,stderr=subprocess.STDOUT,**kw)
 m0=wait(lambda:read(manager)if alive(read(manager))and read(manager).get('first_frame_seen')and 'INSTALLER=catalog|apps=1'in text(manager)else None,20,'Manager real catalog frame');time.sleep(.8);matrix.screenshot('manager-catalog',shots)
 print('PHYSICAL_OPEN_BUTTON',matrix.tap(280,780),flush=True)
 q0=wait(lambda:read(qq)if alive(read(qq))and read(qq).get('component')==str(root)else None,8,'Native OpenApplication did not start QQ')
 wait(lambda:'SDHOST=java_window_bound'in text(qq),20,'QQ host ART/window bind');assert alive(m0);result['native_open_application']=dict(pid=q0['pid'],launch_id=q0['launch_id']);print('NATIVE_OPEN_APPLICATION=PASS|trigger=physical-installer-button|qq_pid='+str(q0['pid']),flush=True)
 close(qq)
 # Deliver a real local APK URI to the existing Manager. Confirm UI only;
 # never press Install and never change installed application records.
 uri=(root/'share/manager.apk').as_uri();previous=text(manager).count('INSTALLER=confirm|file=manager.apk');r=call(['--manager','--install',uri],seconds=20);print('EXISTING_APK_REQUEST',r.returncode,r.stdout.strip(),r.stderr.strip(),flush=True);assert r.returncode==0
 wait(lambda:text(manager).count('INSTALLER=confirm|file=manager.apk')>previous,5,'Existing Manager did not receive APK Intent');m1=read(manager);assert m1['launch_id']==m0['launch_id']and(m1['pid'],m1['start_ticks'])==(m0['pid'],m0['start_ticks']);matrix.screenshot('existing-manager-apk-confirm',shots)
 assert 'INSTALLER=installed'not in text(manager);assert hashlib.sha256(source.read_bytes()).hexdigest()==before_hash
 result['existing_apk_request']=dict(pid=m1['pid'],launch_id=m1['launch_id'],confirmation_only=True);result['status']='PASS';print('NATIVE_INSTALLER_INTERFACES=PASS|native-open=true|existing-apk-request=true|same-host=true|no-install=true',flush=True)
finally:
 errors=[]
 for name in [qq,manager,'org.saildroid.binder']:
  r=read(name)
  if r.get('log')and Path(r['log']).exists():(out/(name+'.log')).write_bytes(Path(r['log']).read_bytes())
  try:close(name)
  except Exception as e:errors.append(str(e))
 identity=rt/'host-manager.state'
 if identity.exists():
  r=json.loads(identity.read_text())
  if alive(r)and(Path('/proc')/str(r['pid'])/'exe').resolve()==root/'libexec/saildroid-host':os.kill(r['pid'],signal.SIGTERM)
 subprocess.run(['mcetool','--set-never-blank=disabled','--set-blank-timeout=8','--blank-screen'],timeout=5)
 for _ in range(50):
  if Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0':break
  time.sleep(.1)
 if watch is not None:watch.terminate();watch.wait(timeout=3)
 result['brightness']=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('FINAL_BRIGHTNESS',result['brightness'],flush=True)
 assert not errors,errors;assert result['brightness']=='0'and boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and lip==subprocess.check_output(['pidof','lipstick'],text=True).strip()
