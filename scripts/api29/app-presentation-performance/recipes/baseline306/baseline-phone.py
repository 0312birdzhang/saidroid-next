from pathlib import Path
import os,json,time,subprocess,pwd,hashlib,shutil,traceback
PKG='com.tencent.mobileqq';BASE=Path('/home/art/test/qq-cover-perf306-baseline-v1');BASE.mkdir(mode=0o700);RT=Path('/run/user/100000/saildroid');ROOT=Path(CFG['candidate']);boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();lip=subprocess.check_output(['pidof','lipstick'],text=True).strip()
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text() and boot==CFG['boot'] and lip==CFG['lipstick'] and str(Path('/home/art/api29-root').resolve())==CFG['daily']
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('qq-cover-perf306-baseline|')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=ROOT/'install-manifest.json';assert sha(manifest)==CFG['manifest_sha256'];m=json.loads(manifest.read_text())
for n,v in m['files'].items():
 p=ROOT/n;assert p.is_file()and not p.is_symlink()and p.stat().st_size==v['size']and (p.stat().st_mode&0o777)==v['mode']and sha(p)==v['sha256'],n
app=Path('/home/art/apps')/PKG;installation=json.loads((app/'record.json').read_text());assert sha(Path(installation['apk']))==CFG['app']['apk_sha256'];(BASE/'apk-record-private.json').write_text(json.dumps(installation,indent=2));(BASE/'apk-record-private.json').chmod(0o600)
u=pwd.getpwnam('defaultuser');env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket');kw=dict(env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid))
result=dict(scope='One isolated candidate r305 QQ cold launch, no account/login/message actions; bounded observation, real exits retained.',boot=boot,lipstick=lip,root=str(ROOT),manifest_sha256=CFG['manifest_sha256'],apk_sha256=CFG['app']['apk_sha256'],manifest_files_verified=len(m['files']),started_epoch=time.time(),observations=[],screenshots=[],natural_exit=False);child=None;watch=None;record=None

def alive(r):
 try:
  p=Path('/proc')/str(r['pid']);f=(p/'stat').read_text().rsplit(') ',1)[1].split()
  return r.get('boot')==boot and int(f[19])==r['start_ticks'] and f[0]not in ['Z','X'] and (p/'exe').resolve()==Path(r['component'])/'libexec/saildroid-host'
 except (OSError,KeyError,ValueError):return False

def states():
 out=[]
 for p in RT.glob(PKG+'*.json'):
  try:r=json.loads(p.read_text());out.append((p,r))
  except (OSError,ValueError):pass
 return out

def preserve(tag):
 folder=BASE/tag;folder.mkdir(mode=0o700)
 for p,r in states():
  shutil.copyfile(p,folder/p.name);(folder/p.name).chmod(0o600);log=Path(r.get('log','/none'))
  if log.is_file():shutil.copyfile(log,folder/(p.stem+'.log'));(folder/(p.stem+'.log')).chmod(0o600)
 source=app/'data/databases/bugly_db_'
 for suffix in ['', '-wal','-shm']:
  p=Path(str(source)+suffix)
  if p.is_file():shutil.copyfile(p,folder/('bugly.db'+suffix));(folder/('bugly.db'+suffix)).chmod(0o600)

assert not any(alive(r) for _,r in states()),'QQ already running; preserve state and stop without duplicate launch'
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:exe=str((proc/'exe').resolve())
 except OSError:continue
 assert not(exe.startswith('/home/art/releases/')and exe.endswith('/libexec/saildroid-host')),'Start requires quiescent SailDroid hosts'

preserve('before')

def capture(tag):
 directory=Path(u.pw_dir)/'Downloads/SailDroid-Screenshots'/BASE.name;directory.mkdir(exist_ok=True);os.chown(directory,u.pw_uid,u.pw_gid);p=directory/(tag+'.png')
 assert not p.exists()
 q=subprocess.run(['gdbus','call','--session','--dest','org.nemomobile.lipstick','--object-path','/org/nemomobile/lipstick/screenshot','--method','org.nemomobile.lipstick.saveScreenshot',str(p)],capture_output=True,text=True,timeout=5,env=env)
 time.sleep(.5)
 if q.returncode==0 and p.exists():
  data=p.read_bytes();assert data[:8]==bytes.fromhex('89504e470d0a1a0a');target=BASE/(tag+'.png');target.write_bytes(data);target.chmod(0o600);result['screenshots'].append(dict(file=target.name,bytes=len(data),sha256=sha(target),width=int.from_bytes(data[16:20],'big'),height=int.from_bytes(data[20:24],'big')))
 else:result['screenshot_error']=dict(code=q.returncode,stderr=q.stderr)

try:
 # Independent process is armed before wake and survives a dead SSH/session.
 watch=subprocess.Popen(['python3','-c',"import subprocess,time;time.sleep(155);subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],timeout=5)"],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 result['watchdog_pid']=watch.pid;assert watch.poll()is None
 subprocess.run(['mcetool','--set-never-blank=disabled','--unblank-screen','--set-tklock-mode=unlocked'],check=True,capture_output=True,timeout=5)
 import shlex
 ident='org.saildroid.app.p'+hashlib.sha256(PKG.encode()).hexdigest()[:20];desktop=Path(u.pw_dir)/'.local/share/applications'/(ident+'.desktop');entries=[line[5:]for line in desktop.read_text().splitlines()if line.startswith('Exec=')];assert len(entries)==1;command=shlex.split(entries[0]);assert command==[str(ROOT/'libexec/saildroid-app'),'--package',PKG,'--desktop-token',PKG];result['desktop_exec']=entries[0];result['desktop_file']=str(desktop)
 with (BASE/'entry.log').open('ab',buffering=0) as stream:child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,**kw)
 result['launch_pid']=child.pid;started=time.monotonic();next_wake=started+15;shot_done=False;done=set();offset=0;timeline=[];samples=[];sample_next=0
 while time.monotonic()-started<140:
  elapsed=time.monotonic()-started
  if record is None:
   candidates=[r for _,r in states()if r.get('pid')==child.pid and r.get('component')==str(ROOT) and r.get('boot')==boot]
   if candidates:record=candidates[0];result['launch_id']=record.get('launch_id');result['main_start_ticks']=record.get('start_ticks')
  current=next((r for _,r in states()if record and r.get('launch_id')==record.get('launch_id')and r.get('role')!='service'),None)
  living=alive(current)if current else False
  row=dict(elapsed_seconds=round(elapsed,3),child_code=child.poll(),main_alive=living,state=current.get('state')if current else None,pid=current.get('pid')if current else None,brightness=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip())
  result['observations'].append(row);print('QQ_CURRENT_PROGRESS='+json.dumps(row),flush=True)
  if child.poll()is not None:
   result.update(natural_exit=True,natural_exit_code=child.returncode,lifetime_seconds=round(elapsed,3));break
  if record:
   log=Path(record['log']);data=log.read_bytes()
   if len(data)>offset:
    text=data[offset:].decode(errors='replace');offset=len(data)
    keys=['SDHOST=','SDRUNTIME=','SDHWUI=','SDACTIVITY=','SDWINDOW_SESSION=','SDWINDOW=','GC freed','SDINPUT=','Choreographer','Skipped']
    timeline.extend(dict(seconds=round(elapsed,4),line=line.replace(chr(0),''))for line in text.splitlines()if any(k in line for k in keys))
   if elapsed>=sample_next:
    tasks=[]
    for p in (Path('/proc')/str(record['pid'])/'task').iterdir():
     try:
      raw=(p/'stat').read_text();f=raw.rsplit(') ',1)[1].split();tasks.append(dict(tid=int(p.name),name=raw[raw.index('(')+1:raw.rindex(')')],ticks=int(f[11])+int(f[12]),state=f[0]))
     except OSError:pass
    samples.append(dict(seconds=elapsed,tasks=tasks,io=(Path('/proc')/str(record['pid'])/'io').read_text(),status=(Path('/proc')/str(record['pid'])/'status').read_text()));sample_next=elapsed+1
  for second in [15,30,45,65]:
   tag='startup-'+str(second)
   if living and elapsed>=second and tag not in done:capture(tag);done.add(tag)
  if living and 70<=elapsed<85:
   second=int((elapsed-70)/2)
   if second not in done:
    done.add(second);args=['swipe','540','1550','540','650','400','24']if second%2==0 else['swipe','540','650','540','1550','400','24']
    subprocess.run(['/home/art/bin/sdinput',*args],check=True,capture_output=True,timeout=5);timeline.append(dict(seconds=round(time.monotonic()-started,4),line='PROBE_SCROLL='+str(second)))
  for second in [90,112]:
   tag='cover-'+str(second)
   if living and elapsed>=second and tag not in done:
    done.add(tag);before=Path(record['log']).read_text(errors='replace').count('SDACTIVITY=host_visibility|foreground=false')
    subprocess.run(['/home/art/bin/sdinput','swipe','1079','800','400','800','300','24'],check=True,capture_output=True,timeout=5)
    time.sleep(1.5);capture(tag)
    background=Path(record['log']).read_text(errors='replace').count('SDACTIVITY=host_visibility|foreground=false')>before
    result.setdefault('cover_cycles',[]).append(dict(tag=tag,physical_edge_swipe=True,background_marker=background,same_main_alive=alive(record)))
    q=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,timeout=10,**kw);assert q.returncode==0
    time.sleep(1);capture('resumed-'+str(second))
  if elapsed>=next_wake-started:
   subprocess.run(['mcetool','--unblank-screen'],check=True,capture_output=True,timeout=5);next_wake=time.monotonic()+15
  time.sleep(.2)
 (BASE/'timeline.json').write_text(json.dumps(timeline,indent=2));(BASE/'task-samples.json').write_text(json.dumps(samples));result['observed_window_seconds']=round(time.monotonic()-started,3);result['same_main_alive_at_observation_end']=bool(record and alive(record));preserve('observed-end')
except BaseException as error:
 result['probe_error']=repr(error);traceback.print_exc()
finally:
 result['ended_epoch_before_cleanup']=time.time()
 # Preserve natural outcome before any explicit close. Close only this launch family.
 try:
  if not (BASE/'observed-end').exists():preserve('observed-end')
  if record:
   for _,r in states():
    owned=r.get('launch_id')==record.get('launch_id')or r.get('owner_launch_id')==record.get('launch_id')
    if not owned or r.get('component')!=str(ROOT)or not alive(r):continue
    args=[str(ROOT/'libexec/saildroid-app'),'--package',PKG]
    if r.get('role')=='service':args+=['--service',r.get('service')or PKG,'--process',r['process_name']]
    q=subprocess.run(args+['--close'],capture_output=True,text=True,timeout=18,**kw);result.setdefault('explicit_cleanup',[]).append(dict(pid=r['pid'],code=q.returncode))
  if child is not None:
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:result['cleanup_child_alive']=True
 except BaseException as error:result['cleanup_error']=repr(error)
 preserve('after-cleanup')
 result['display_cleanup']=blank_display()
 if watch is not None and result['display_cleanup']['ready']:
  watch.terminate();watch.wait(timeout=3)
 result['boot_after']=Path('/proc/sys/kernel/random/boot_id').read_text().strip();result['lipstick_after']=subprocess.check_output(['pidof','lipstick'],text=True).strip();result['daily_after']=str(Path('/home/art/api29-root').resolve());result['qq_remaining']=[dict(pid=r.get('pid'),launch_id=r.get('launch_id'),role=r.get('role'))for _,r in states()if alive(r)]
 result['apk_unchanged']=sha(Path(installation['apk']))==CFG['app']['apk_sha256'];result['cleanup_safe']=result['display_cleanup']['ready']and not result['qq_remaining']and not result.get('cleanup_error')and not result.get('cleanup_child_alive')and result['boot_after']==boot and result['lipstick_after']==lip and result['daily_after']==CFG['daily']
 (BASE/'result.json').write_text(json.dumps(result,indent=2)+'\n');(BASE/'result.json').chmod(0o600);print('QQ_CURRENT_TERMINAL='+json.dumps(result),flush=True)
 assert result['cleanup_safe'],'QQ probe cleanup unsafe'
