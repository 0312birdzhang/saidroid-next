"""One isolated official instrumentation run under an existing device lock.
CONFIG supplied by the reviewed VM orchestration; no root privileges in tests.
"""
from pathlib import Path
import os,pwd,json,hashlib,subprocess,time,zipfile,shutil,signal,base64
assert Path('/home/art/test/.device-lock/owner').read_text().startswith('cts-module-run|')
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text()
label=CONFIG['label'];assert label.replace('-','').isalnum();base=Path('/home/art/test')/label
assert base.is_dir()and not base.is_symlink();root=Path(CONFIG['root']);assert root.is_dir()and root.resolve()==root and not root.is_symlink()and root.parent in[Path('/home/art/releases'),Path('/opt/saildroid/releases')]
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert not CONFIG.get('expected_boot')or CONFIG['expected_boot']==boot,'Suite boot identity changed';lip=subprocess.check_output(['pidof','lipstick'],text=True).strip();active=Path('/home/art/api29-root').resolve();u=pwd.getpwnam('defaultuser');installed=[];record=None;p=None;watch=None;pushed=[];created_dirs=[]
visible_seconds=CONFIG.get('visible_seconds',0);assert isinstance(visible_seconds,int)and 0<=visible_seconds<=60
visible_watch=None
file_trace=None
process_maps=None
native_stacks_captured=False
native_test_observed_at=None
policy_grant=None
cts_directory_state={}
pkg=CONFIG['package'];result=dict(module=CONFIG['module'],package=pkg,status='ERROR',boot=boot,lipstick=lip,runtime=str(root),formal_tradefed=False,api=29,run=label)
env=dict(os.environ,HOME=u.pw_dir,USER=u.pw_name,LOGNAME=u.pw_name,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket');kw=dict(env=env,user=u.pw_uid,group=u.pw_gid,extra_groups=os.getgrouplist(u.pw_name,u.pw_gid));host=str(root/'libexec/saildroid-app')
if CONFIG.get('linker_verbose'):env['SAILDROID_LINKER_VERBOSE']='1'
env.pop('SAILDROID_NATIVE_FAILURE_DIAGNOSTICS',None)
if CONFIG.get('capture_native_failure'):env['SAILDROID_NATIVE_FAILURE_DIAGNOSTICS']='1'
env.pop('SAILDROID_CFI_TIMING_DIAGNOSTIC',None)
if CONFIG.get('capture_cfi_timing'):
 assert pkg=='org.example.saildroid.mediatiming','CFI timing is confined to the internal media diagnostic'
 env['SAILDROID_CFI_TIMING_DIAGNOSTIC']='1'
def compositor_health():
 probe=Path('/home/art/test/hwui-tools/sd-wayland-health')
 assert probe.is_file(),'Missing real Wayland sync probe'
 try:
  run=subprocess.run([str(probe)],capture_output=True,text=True,timeout=5,**kw)
  return dict(exit=run.returncode,output=run.stdout.strip(),error=run.stderr.strip(),ready=run.returncode==0 and run.stdout.strip()=='WAYLAND_HEALTH=ready|surface_count=0')
 except subprocess.TimeoutExpired:return dict(exit=None,output='',error='Wayland sync probe exceeded 5 seconds',ready=False)
def atomic(path,value):
 pending=path.with_suffix('.pending');pending.write_text(json.dumps(value,indent=2)+'\n');os.replace(pending,path)
def logs():
 found=[]
 for path in Path('/run/user/100000/saildroid').glob(pkg+'*.json'):
  try:r=json.loads(path.read_text())
  except (ValueError,OSError):continue
  log=Path(r.get('log','/nonexistent'))
  if r.get('component')==str(root)and log.is_file():
   out=base/(path.stem+'.log');out.write_bytes(log.read_bytes());out.chmod(0o600);found.append(str(out))
 return found
try:
 result['display_before']=blank_display()
 assert result['display_before']['ready'],'Initial MCE/panel off boundary failed'
 result['compositor_before']=compositor_health()
 assert result['compositor_before']['ready'],'Compositor does not answer real Wayland sync before test'
 watch=subprocess.Popen(['python3','-c',"import subprocess,time;time.sleep("+str(CONFIG['timeout']+15)+");subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"],start_new_session=True)
 if CONFIG.get('directory_preparation'):
  result['directory_preparation']=cts_directory_state
  prepare_directories(CONFIG['directory_preparation'],cts_directory_state,u.pw_uid,u.pw_gid)
 for item in CONFIG.get('pushed_files',[]):
  folder=Path('/data/local/tmp/signature-test');destination=Path(item['destination'])
  assert destination.parent==folder and destination.name==item['file']
  data=Path('/data');assert data.is_dir()and not data.is_symlink()and data.stat().st_uid==0 and data.stat().st_mode&0o022==0
  for directory in [Path('/data/local'),Path('/data/local/tmp'),folder]:
   assert not directory.is_symlink()
   if not directory.exists():directory.mkdir(mode=0o755);created_dirs.append(directory)
   assert directory.is_dir()and directory.stat().st_uid==0 and directory.stat().st_mode&0o022==0
  assert folder.stat().st_uid==0 and folder.stat().st_mode&0o022==0
  assert not destination.exists()and not destination.is_symlink(),'Refuse to replace an existing prepared file'
  source=base/item['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
  shutil.copyfile(source,destination);destination.chmod(0o444);pushed.append((destination,item['sha256']));source.unlink()
 for item in CONFIG['apks']:
  name=item['package'];assert name not in ['android','org.saildroid.manager','org.saildroid.binder','com.tencent.mobileqq'];assert all(c.isalnum()or c in'._'for c in name)
  app=Path('/home/art/apps')/name;assert not app.exists(),'Refuse to replace existing app '+name
  source=base/item['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
  app.mkdir();installed.append((app,item['sha256']));(app/'lib').mkdir();(app/'data').mkdir();(app/'data/files').mkdir()
  shutil.copyfile(source,app/'app.apk')
  with zipfile.ZipFile(source)as z:
   for entry in z.namelist():
    if entry.startswith('lib/arm64-v8a/')and entry.endswith('.so'):
     target=app/'lib'/Path(entry).name;assert target.name==entry[len('lib/arm64-v8a/'):];target.write_bytes(z.read(entry));target.chmod(0o755)
  (app/'icon.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='))
  atomic(app/'record.json',dict(package=name,apk=str(app/'app.apk'),native=str(app/'lib'),icon=str(app/'icon.png'),data=str(app/'data'),cts_run=label,apkSha256=item['sha256'],debuggable=item.get('debuggable',False)))
  for f in [app,*app.rglob('*')]:os.chown(f,u.pw_uid,u.pw_gid)
  assert hashlib.sha256((app/'app.apk').read_bytes()).hexdigest()==item['sha256']
  source.unlink() # Keep the installed, verified copy; do not transfer duplicate APKs back.
 app=Path('/home/art/apps')/pkg;assert app.is_dir()
 configs=[]
 for item in CONFIG.get('dynamic_configs',[]):
  assert Path(item['name']).name==item['name']and item['name'].endswith('.dynamic')
  source=base/item['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
  folder=app/'data/files/cts-config';folder.mkdir(exist_ok=True);os.chown(folder,u.pw_uid,u.pw_gid)
  target=folder/item['name'];assert not target.exists();shutil.copyfile(source,target);os.chown(target,u.pw_uid,u.pw_gid);source.unlink()
  configs.append(dict(name=item['name'],path=str(target),sha256=item['sha256']))
 request=app/'data/files/instrument-request.json'
 settings=dict(run_id=label,component=CONFIG['component'],arguments=CONFIG['arguments'],dynamic_configs=configs)
 if CONFIG.get('network_proxy'):
  import ipaddress
  proxy=CONFIG['network_proxy'];address=ipaddress.IPv4Address(proxy['host'])
  assert proxy['type']=='socks5'and not address.is_unspecified and not address.is_multicast and type(proxy['port'])is int and 1024<=proxy['port']<=65535
  settings['network_proxy']=dict(type='socks5',host=str(address),port=proxy['port'])
 if CONFIG.get('hidden_api_checks',True)is False:
  folder=Path('/home/art/test/cts-run-policies')
  if not folder.exists():folder.mkdir(mode=0o755)
  info=folder.lstat();assert not folder.is_symlink()and folder.resolve()==folder and info.st_uid==0 and info.st_mode&0o022==0
  grant_file=folder/(label+'.json');assert not grant_file.exists()and not grant_file.is_symlink()
  settings['official_policy_grant']=str(grant_file)
 atomic(request,settings);os.chown(request,u.pw_uid,u.pw_gid)
 if CONFIG.get('hidden_api_checks',True)is False:
  assert len(CONFIG['official_config_sha256'])==64
  grant=dict(schema='saidroid-official-instrumentation-policy-v1',boot=boot,component_root=str(root),package=pkg,run_id=label,instrumentation=CONFIG['component'],request_sha256=hashlib.sha256(request.read_bytes()).hexdigest(),apk_sha256=hashlib.sha256((app/'app.apk').read_bytes()).hexdigest(),hidden_api_checks=False,official_config_sha256=CONFIG['official_config_sha256'],expires_monotonic_us=int((time.monotonic()+CONFIG['timeout']+120)*1000000))
  content=(json.dumps(grant,sort_keys=True)+'\n').encode()
  fd=os.open(grant_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o644)
  info=os.fstat(fd);policy_grant=dict(path=grant_file,device=info.st_dev,inode=info.st_ino,sha256=None)
  with os.fdopen(fd,'wb')as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
  grant_file.chmod(0o444);policy_grant['sha256']=hashlib.sha256(content).hexdigest()
  result['official_hidden_api_policy']=dict(checks=False,config_sha256=CONFIG['official_config_sha256'],grant_sha256=policy_grant['sha256'],scope='single-process-root-owned-run-grant')
 if visible_seconds:
  # Explicit diagnostic window only. The full batch defaults to OLED off.
  # This independent process blanks even if the instrumentation thread stalls.
  visible_watch=subprocess.Popen(['python3','-c',"import subprocess,time;time.sleep("+str(visible_seconds)+");subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'])"],start_new_session=True)
  subprocess.run(['mcetool','--unblank-screen'],check=True,timeout=5)
  until=time.monotonic()+3
  while time.monotonic()<until and Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()=='0':time.sleep(.05)
  assert Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()!='0','Bounded visible diagnostic failed to wake output'
  result['visible_diagnostic_seconds']=visible_seconds
 with(base/'entry.log').open('w')as out:p=subprocess.Popen([host,'--package',pkg,'--instrument-request',str(request),'--debug-log'],stdout=out,stderr=subprocess.STDOUT,**kw)
 deadline=time.monotonic()+CONFIG['timeout'];complete=app/'data/files/instrumentation'/label/'result.json';events=complete.with_name('events.jsonl');state=Path('/run/user/100000/saildroid')/(pkg+'.json')
 while time.monotonic()<deadline:
  if CONFIG.get('capture_process_maps'):
   maps=Path('/proc')/str(p.pid)/'maps'
   try:
    value=maps.read_bytes();assert len(value)<=2*1024*1024
    if value and p.poll()is None:process_maps=value
   except FileNotFoundError:pass
  if state.exists():
   value=json.loads(state.read_text())
   if value.get('pid')==p.pid:record=value
  if CONFIG.get('trace_rs_files')and file_trace is None:
   assert pkg=='android.renderscript.cts'
   status=Path('/proc')/str(p.pid)/'status'
   if status.exists():
    fields=dict(line.split(':',1)for line in status.read_text().splitlines()if ':'in line)
    # Attach after bootstrap has dropped its temporary capability, so tracing
    # cannot suppress the file capability needed to establish process limits.
    # This 4.9 kernel omits NoNewPrivs from /proc/status. The exact native
    # host executable is reached only after bootstrap has dropped capabilities.
    if int(fields.get('CapEff','0').strip(),16)==0 and fields.get('Uid','').split()==[str(u.pw_uid)]*4 and (Path('/proc')/str(p.pid)/'exe').resolve()==root/'libexec/saildroid-host':
     tracer=shutil.which('strace');assert tracer,'strace unavailable for explicit compiler-file diagnostic'
     with(base/'rs-files-tracer.log').open('w')as diagnostic:
      file_trace=subprocess.Popen([tracer,'-f','-qq','-s','256','-e','trace=%file','-o',str(base/'rs-files.trace'),'-p',str(p.pid)],stdout=subprocess.DEVNULL,stderr=diagnostic)
  if CONFIG.get('capture_rs_native_stacks')and native_test_observed_at is None and events.exists():
   for raw in events.read_text().splitlines():
    try:observed=json.loads(raw)
    except ValueError:continue
    if observed.get('event')=='status'and observed.get('code')==1 and observed.get('bundle',{}).get('test'):
     native_test_observed_at=time.monotonic();break
  if CONFIG.get('capture_rs_native_stacks')and not native_stacks_captured and native_test_observed_at is not None and time.monotonic()>native_test_observed_at+3:
   assert pkg=='android.renderscript.cts'
   status=Path('/proc')/str(p.pid)/'status'
   if status.exists():
    fields=dict(line.split(':',1)for line in status.read_text().splitlines()if ':'in line)
    if int(fields.get('CapEff','0').strip(),16)==0 and fields.get('Uid','').split()==[str(u.pw_uid)]*4 and (Path('/proc')/str(p.pid)/'exe').resolve()==root/'libexec/saildroid-host':
     native_stacks_captured=True
     debugger=shutil.which('gdb');assert debugger,'gdb unavailable for explicit native-stack diagnostic'
     command=[debugger,'-nx','-batch','-iex','set auto-solib-add off','-iex','set auto-load safe-path /nonexistent','-ex','set pagination off']
     # These Android DSOs are mapped by the private linker, outside glibc's
     # link_map. Register their real load addresses for symbols and CFI.
     # Include stripped, bounded Android libraries; skip large compiler DSOs.
     addresses={}
     for line in (Path('/proc')/str(p.pid)/'maps').read_text().splitlines():
      fields=line.split()
      if len(fields)!=6:continue
      file=Path(fields[5])
      if file.parent!=root/'android-libs' or file.suffix!='.so' or not file.is_file() or file.stat().st_size>16*1024*1024:continue
      address=int(fields[0].split('-')[0],16)-int(fields[2],16)
      addresses[file]=min(addresses.get(file,address),address)
     for file,address in addresses.items():command+=['-ex','add-symbol-file '+str(file)+' -o '+hex(address)]
     command+=['-ex','thread apply all bt 18','-ex','detach','-p',str(p.pid)]
     try:
      capture=subprocess.run(command,capture_output=True,timeout=10)
      data=capture.stdout+capture.stderr;assert len(data)<=4*1024*1024
      (base/'rs-native-stacks.txt').write_bytes(data)
      result['native_stacks_exit']=capture.returncode
      if p.poll()is None:
       try:
        java_capture=subprocess.run([host,'--package',pkg,'--dump-threads'],capture_output=True,timeout=5,**kw)
        (base/'rs-java-stack-request.log').write_bytes(java_capture.stdout+java_capture.stderr)
        result['java_stack_request_exit']=java_capture.returncode
       except subprocess.TimeoutExpired:result['java_stack_request_timeout']=True
     except subprocess.TimeoutExpired as failure:
      (base/'rs-native-stacks.txt').write_bytes((failure.stdout or b'')+(failure.stderr or b''))
      result['native_stacks_timeout']=True
  if complete.exists():
   value=json.loads(complete.read_text());result['instrumentation']=value
   result['status']='COMPLETED'if value['code']==-1 else'RUNNER_FAILED';break
  if p.poll()is not None:result.update(status='PROCESS_EXIT',exit=p.returncode);break
  time.sleep(.1)
 else:result['status']='TIMEOUT'
 if events.exists():(base/'instrumentation-events.jsonl').write_bytes(events.read_bytes())
 if complete.exists():shutil.copyfile(complete,base/'instrumentation-result.json')
 if CONFIG.get('capture_rs_cache'):
  assert pkg in['android.renderscript.cts','android.renderscriptlegacy.cts','android.rscpp.cts'],'Compiler cache capture is limited to official RS diagnostics'
  saved=[];size=0
  for file in(app/'data').rglob('*'):
   if not file.is_file()or file.is_symlink()or file.suffix not in['.so','.o','.bc']:continue
   assert file.resolve().is_relative_to((app/'data').resolve())
   size+=file.stat().st_size;assert len(saved)<24 and size<=32*1024*1024,'Bounded compiler diagnostic artifacts'
   target=base/'rs-cache'/file.relative_to(app/'data');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,target);target.chmod(0o600)
   saved.append(dict(path=str(target.relative_to(base)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size))
  atomic(base/'rs-cache-manifest.json',dict(files=saved))
 result['logs']=logs();result['pid']=p.pid
except Exception as failure:
 result.update(status='ERROR',reason=str(failure));result['logs']=logs()
finally:
 if process_maps:(base/'process-maps.txt').write_bytes(process_maps)
 if file_trace is not None:
  file_trace.terminate()
  try:file_trace.wait(timeout=3)
  except subprocess.TimeoutExpired:file_trace.kill();file_trace.wait(timeout=3)
  result['file_trace_exit']=file_trace.returncode
 for args in [[host,'--package',pkg,'--close']]:
  try:subprocess.run(args,capture_output=True,timeout=22,**kw)
  except subprocess.TimeoutExpired:result['cleanup_timeout']=True
 # Headless secondary services can outlive a timed-out instrumentation thread.
 # Close only the fresh identities of this exact test family before the broker.
 for state in Path('/run/user/100000/saildroid').glob(pkg+'*.json'):
  try:
   child=json.loads(state.read_text())
   if child.get('boot')!=boot or child.get('component')!=str(root) or child.get('role')!='service' or not record or child.get('owner_launch_id')!=record.get('launch_id'):continue
   proc=Path('/proc')/str(child['pid'])
   parts=(proc/'stat').read_text().rsplit(') ',1)[1].split()
   if parts[0]in['Z','X']or int(parts[19])!=child['start_ticks']:continue
   if(proc/'exe').resolve()!=root/'libexec/saildroid-host':raise RuntimeError('Secondary executable identity differs')
   subprocess.run([host,'--package',pkg,'--service',child.get('service')or pkg,'--process',child['process_name'],'--close'],capture_output=True,timeout=22,**kw)
  except FileNotFoundError:pass
  except subprocess.TimeoutExpired:result['cleanup_timeout']=True
 try:subprocess.run([host,'--broker','--close'],capture_output=True,timeout=22,**kw)
 except subprocess.TimeoutExpired:result['cleanup_timeout']=True
 if p is not None:
  try:p.wait(timeout=7)
  except subprocess.TimeoutExpired:result['cleanup_process_alive']=True
 logs()
 for app,sha in installed:
  try:
   for state in Path('/run/user/100000/saildroid').glob(app.name+'*.json'):
    value=json.loads(state.read_text());proc=Path('/proc')/str(value.get('pid',0))
    if value.get('boot')!=boot:continue
    if proc.exists():
     parts=(proc/'stat').read_text().rsplit(') ',1)[1].split();assert parts[0]in['Z','X']or int(parts[19])!=value.get('start_ticks'),'Test process still alive'
   assert hashlib.sha256((app/'app.apk').read_bytes()).hexdigest()==sha
   assert json.loads((app/'record.json').read_text())['cts_run']==label
   shutil.rmtree(app)
  except Exception as failure:result['cleanup_error']=str(failure)
 if policy_grant is not None:
  try:
   grant_file=policy_grant['path'];info=grant_file.lstat()
   assert not grant_file.is_symlink()and info.st_uid==0 and info.st_dev==policy_grant['device']and info.st_ino==policy_grant['inode']and info.st_nlink==1
   if policy_grant['sha256']is not None:assert hashlib.sha256(grant_file.read_bytes()).hexdigest()==policy_grant['sha256']
   grant_file.unlink();result['policy_grant_removed']=True
  except Exception as failure:result['cleanup_error']='Official policy grant cleanup: '+str(failure)
 for path,sha in pushed:
  try:
   assert path.is_file()and not path.is_symlink()and hashlib.sha256(path.read_bytes()).hexdigest()==sha
   path.unlink()
  except Exception as failure:result['cleanup_error']='Prepared file cleanup: '+str(failure)
 for path in reversed(created_dirs):
  try:path.rmdir()
  except Exception as failure:result['cleanup_error']='Prepared directory cleanup: '+str(failure)
 if cts_directory_state:
  try:
   assert not any(result.get(key)for key in ['cleanup_timeout','cleanup_process_alive','cleanup_error']),'Retain scratch while owned process cleanup is unproven'
   cleanup_directories(cts_directory_state)
  except Exception as failure:result['cleanup_error']='Libcore scratch cleanup: '+str(failure)
 # mcetool returns after submitting the request, before the panel finishes
 # blanking. Keep the independent watchdog until actual brightness and MCE
 # both confirm off. Do not alter test timing or any original test result.
 result['display_cleanup']=blank_display()
 if visible_watch is not None:visible_watch.terminate();visible_watch.wait(timeout=3)
 if watch is not None:watch.terminate();watch.wait(timeout=3)
 result['brightness']=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip()
 result['boot_unchanged']=boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip();result['lipstick_unchanged']=lip==subprocess.check_output(['pidof','lipstick'],text=True).strip();result['daily_root_unchanged']=active==Path('/home/art/api29-root').resolve()
 result['compositor_after']=compositor_health()
 atomic(base/'run-result.json',result);print('MODULE_RUN='+json.dumps({k:v for k,v in result.items()if k not in['logs','instrumentation']}),flush=True)
 assert result['display_cleanup']['ready']and result['brightness']=='0'and result['boot_unchanged']and result['lipstick_unchanged']and result['daily_root_unchanged']
 assert result.get('compositor_before',{}).get('ready')and result['compositor_after']['ready'],'Compositor sync failed; stop serial suite and preserve raw test events'
 assert not any(result.get(k)for k in ['cleanup_timeout','cleanup_process_alive','cleanup_error']),result
