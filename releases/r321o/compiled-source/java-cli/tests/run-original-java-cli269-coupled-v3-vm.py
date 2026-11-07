from pathlib import Path
import os,sys,subprocess,json,hashlib,fcntl,struct,time,shutil,collections,zipfile
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');base=repo/'build/evidence/cts-frame-repair-20261031';draft=base/'keystore-drafts/attestation194-v1';version='main226-v2';case='six-whole-global-state-classes-declared-listener';result_name='original-java-cli269-'+('after'if '--after'in sys.argv else'before')+'-v3';built=Path('/var/lib/saidroid-standard-keystore194-combined-draft-v1');workspace=Path('/var/lib/saidroid-'+result_name);work=workspace/'run';bridge=Path('/var/lib/saidroid-java-binder194-v4');component=Path('/var/tmp/saidroid-java-cli268-prototype-v4/root'if '--after'in sys.argv else'/var/tmp/saidroid-pem-empty266-v1-formal-vm-component/root');clone=Path('/var/tmp/saidroid-unprivileged182-runtime-20261031');platform=Path('/var/tmp/saidroid-readable-android-product-runtime-20261031');native=Path('/var/tmp/saidroid-softkeymaster194-contract-v6/lib');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();art_candidate=component/'lib/libart.so';art_manifest=json.loads((base/'art240-host-math-precision-v1-build.json').read_text());assert art_manifest['passed']and sha(art_candidate)==art_manifest['binary_sha256']
if '--inside'not in sys.argv:
 prior_smoke=json.loads((base/'original-main226-full-v3.json').read_text());assert all(prior_smoke.get(n)for n in ['private_state_and_apk_removed','owned_processes_reaped','binderfs_removed','private_bus_removed','private_data_mount_removed'])
 failed_preflight=json.loads((base/'original-main226-full-v1.json').read_text());assert all(failed_preflight.get(n)for n in ['private_state_and_apk_removed','owned_processes_reaped','binderfs_removed','private_bus_removed','private_data_mount_removed'])
 prior_full=json.loads((base/'original-main199-full-v1.json').read_text())
 assert all(prior_full.get(n)for n in ['private_state_and_apk_removed','owned_processes_reaped','binderfs_removed','private_bus_removed','private_data_mount_removed']), 'Previous full original runner must terminate naturally and finish cleanup before another Binder fixture'
 assert not (bridge/'binderfs').exists(), 'Previous Binder fixture not removed'
 frozen=json.loads((base/'original-java-cli269-coupled-v3-frozen-inputs.json').read_text())
 for name,digest in frozen['sources'].items():assert sha(repo/name)==digest,name
 for name,digest in frozen['proofs'].items():assert sha(base/name)==digest,name
 reconstructed=json.loads((base/('java-cli268-prototype-v4.json'if '--after'in sys.argv else'pem-empty266-v1-formal-vm-root-reconstruction.json')).read_text());assert reconstructed['passed']and reconstructed['root']==str(component)
 manifest=json.loads((component/'install-manifest.json').read_text())
 for name,entry in manifest['files'].items():
  p=component/name;assert p.is_file()and not p.is_symlink()and sha(p)==entry['sha256']and (p.stat().st_mode&0o777)==entry['mode'],name
 assert {str(p.relative_to(component)):os.readlink(p)for p in component.rglob('*')if p.is_symlink()}==manifest['symlinks']
 prior=json.loads((base/'original-keystore194-encoded-keystore-class-v2.json').read_text());assert prior['passed']and prior['counts']==dict(started=29,passed=29)and all(prior[n]for n in['owned_processes_reaped','binderfs_removed','private_state_and_apk_removed']);assert prior['actual_server_boot_images'],'Actual new boot images must be proven first'
 build=json.loads((built/'manifest.json').read_text());assert build['passed']and sha(built/'libsoftware-keystore.so')==build['library_sha256'];assert sha(built/'contract.jar')==build['jar_sha256'];other=Path('/var/lib/saidroid-standard-keystore194-v13');assert sha(built/'classes/KeystoreInstrumentationBootstrap.class')==sha(other/'classes/KeystoreInstrumentationBootstrap.class')and sha(built/'classes/StandaloneKeystoreServer.class')==sha(other/'classes/StandaloneKeystoreServer.class')
 for n,h in build['sources'].items():assert sha(draft/n)==h
 workspace.mkdir(mode=0o755)
 inputs=workspace/'original-inputs';inputs.mkdir(mode=0o755);sys.path.insert(0,str(repo/'scripts/cts'));from official_archive import Archive
 module=next(m for m in json.loads((base/'module-plan.json').read_text())['modules']if m['module']=='CtsLibcoreTestCases');archive=Archive(base/'official-index.json');metadata=archive.extract('android-cts/testcases/CtsLibcoreTestCases.apk',inputs/'original.apk');assert metadata['sha256']=='1a556a2b9f9b5a98ce05741cd20076e6b18c89458df7d4b280eb03ca413ce4cb';assert archive.extract(module['config_source'],inputs/'original.config')['sha256']==module['config_sha256'];(inputs/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');(inputs/'original.apk').chmod(0o444);(inputs/'original.config').chmod(0o444)
 nss_before={n:sha(Path('/etc')/n)for n in['passwd','group','hosts','nsswitch.conf','resolv.conf']}
 created_data=not Path('/data').exists()
 if created_data:Path('/data').mkdir(mode=0o755)
 data_info=Path('/data').lstat();assert Path('/data').is_dir()and not Path('/data').is_symlink()and data_info.st_uid==0 and not(data_info.st_mode&0o022)
 data_identity=(data_info.st_dev,data_info.st_ino)
 try:
  p=subprocess.run(['unshare','--mount','--pid','--fork','--kill-child=SIGKILL','--',sys.executable,str(Path(__file__).resolve()),'--inside',*([a for a in sys.argv[1:]if a!='--inside'])],capture_output=True,text=True,timeout=12120)
 finally:
  shutil.rmtree(inputs)
  if created_data:
   assert (Path('/data').lstat().st_dev,Path('/data').lstat().st_ino)==data_identity and not list(Path('/data').iterdir());Path('/data').rmdir()
  assert all(sha(Path('/etc')/n)==h for n,h in nss_before.items()),'Host account files changed'
 (base/(result_name+'-driver.log')).write_text(p.stdout+p.stderr);print(p.stdout);print(p.stderr[-3000:],file=sys.stderr);assert p.returncode==0;sys.exit(0)
os.umask(0o022);work.mkdir(mode=0o755);subprocess.run(['mount','--make-rprivate','/'],check=True);subprocess.run(['mount','-t','proc','proc','/proc'],check=True);assert Path('/sys/class/net/lo/operstate').read_text().strip()in['unknown','up']
build=json.loads((built/'manifest.json').read_text());crypto=json.loads((base/'softkeymaster194-v6-contract.json').read_text());assert crypto['passed']
for n,v in crypto['original_library_closure'].items():assert sha(native/n)==v['sha256']
sys.path.insert(0,str(repo/'scripts/cts'));from official_archive import Archive
module=next(m for m in json.loads((base/'module-plan.json').read_text())['modules']if m['module']=='CtsLibcoreTestCases');inputs=workspace/'original-inputs';apk=work/'original.apk';shutil.copyfile(inputs/'original.apk',apk);apk.chmod(0o444);work.chmod(0o755);workspace.chmod(0o755);apk_metadata=json.loads((inputs/'metadata.json').read_text());assert sha(apk)==apk_metadata['sha256']=='1a556a2b9f9b5a98ce05741cd20076e6b18c89458df7d4b280eb03ca413ce4cb';config=work/'original.config';shutil.copyfile(inputs/'original.config',config);assert sha(config)==module['config_sha256'];options={i['name']:i['value']for i in module['runners'][0]['options']};assert options['hidden-api-checks']=='false'and options['shell-timeout']=='12000000'
phone_plan=json.loads((base/'modules/CtsLibcoreTestCases/inputs/plan.json').read_text());assert phone_plan['official_config_sha256']==module['config_sha256']and phone_plan['component']=='android.libcore.cts/androidx.test.runner.AndroidJUnitRunner'
arguments=dict(phone_plan['arguments']);assert arguments=={'filter':'com.android.cts.core.runner.ExpectationBasedFilter','core-expectations':'/knownfailures.txt','timeout_msec':'300000'}
selected_classes=['libcore.java.lang.OldRuntimeTest', 'libcore.java.lang.ProcessBuilderTest', 'org.apache.harmony.tests.java.lang.Process2Test', 'org.apache.harmony.tests.java.lang.ProcessBuilderTest', 'org.apache.harmony.tests.java.lang.ProcessManagerTest', 'org.apache.harmony.tests.java.lang.ProcessTest', 'org.apache.harmony.tests.java.lang.RuntimeTest'];arguments['class']=','.join(selected_classes);assert 'notClass'not in arguments
facade=work/'homeart';facade.mkdir();(facade/'api29-root').symlink_to(component);lib=facade/'lib';lib.mkdir()
for dirname in ['homeart','crypto','icu','artlib']:
 for f in(clone/dirname).iterdir():
  if f.is_file()and not(lib/f.name).exists():(lib/f.name).symlink_to(f)
(lib/'libopenjdk.so').unlink();(lib/'libopenjdk.so').symlink_to('/var/tmp/saidroid-actual-phone-openjdk-20261031/libopenjdk.so')
subprocess.run(['mount','-t','tmpfs','-o','mode=0755,size=4m,nr_inodes=32','tmpfs','/home'],check=True);Path('/home/art').mkdir();subprocess.run(['mount','--bind',str(facade),'/home/art'],check=True)
mount=bridge/'binderfs';mount.mkdir();subprocess.run(['mount','-t','binder','-o','max=1','binder',str(mount)],check=True);control=os.open(mount/'binder-control',os.O_RDONLY|os.O_CLOEXEC);request=bytearray(struct.pack('256sII',b'session',0,0));fcntl.ioctl(control,0xc1086201,request,True);os.close(control);device=mount/'session';device.chmod(0o666)
key_state=work/'key-state';key_state.mkdir(mode=0o700);os.chown(key_state,10050,10050);keyfd=os.open(key_state,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);identities=work/'identities';identities.mkdir(mode=0o700);fixture=Path('/var/lib/saidroid-standard-keystore230-fixture-paths-v4');fixture_meta=json.loads((fixture/'manifest.json').read_text());assert fixture_meta['passed']and sha(fixture/'contract.jar')==fixture_meta['jar_sha256']and fixture_meta['base_manifest_sha256']==sha(built/'manifest.json');runtime=json.loads((component/'runtime.json').read_text());paths=[component/n for n in runtime['boot_jars']]+[fixture/'contract.jar',component/'lib/runtime.jar'];locations=['/home/art/api29-root/'+n for n in runtime['boot_jars']]+list(map(str,paths[len(runtime['boot_jars']):]));processes=[];folders=[];uid=None;result=dict(scope='Seven WHOLE original Runtime/Process/ProcessBuilder classes79 methods in one original APK/defaultApplication/declaredAJUR invocation. Before266 vs prototypeCLI268 only adds actual ordinary-user dalvikvm entry/exactrawART/blacklistedSDK29platformbootstrap; component-private PATH mirrors normal nativehost for both. Parentcore/ART/native/runtime remain byteexact266. Noextra listenerarg/manualreset/VMargs/APK/assertion/filter/heap/budget/clockchanges. Explicit existing VM Binder/softwarekeystore/rootMCE/alternateJNI fixtures; not phone/fullmodule acceptance',passed=False,apk_metadata=apk_metadata,config_sha256=sha(config),selected_class=','.join(selected_classes),original_options=options,build_manifest_sha256=sha(built/'manifest.json'),original_library_closure=crypto['original_library_closure'])
def directory(name,owner):
 p=work/name;p.mkdir(mode=0o700);os.chown(p,owner,owner);folders.append(p);return p
def env(owner,data):
 cfg=data/'config';cfg.mkdir();os.chown(cfg,owner,owner);(cfg/'runtime.cfg').write_text('libc.so libc_bio.so.0\nlibstdc++.so libstdc++_bio.so.0\nlibm.so libm.so.6\nlibdl.so libdl.so.2\n');(cfg/'runtime.cfg').chmod(0o444)
 return dict(PATH=(str(component/'bin')+':/usr/bin:/bin')if owner!=10050 else'/usr/bin:/bin',HOME=str(data),TMPDIR=str(data),LANG='C.UTF-8',LD_LIBRARY_PATH='/var/tmp/saidroid-actual-phone-openjdk-20261031:'+str(component/'lib')+':'+str(clone/'crypto')+':'+str(clone/'icu')+':'+str(clone/'artlib')+':'+str(clone/'patched')+':'+str(bridge/'readable-native')+':'+str(clone/'homeart')+':/usr/local/lib',LD_PRELOAD=str(component/'lib/libsdmath-precision.so')+':'+str(component/'lib/libsdstrictmath-fdlibm.so')+':'+str(component/'lib/libsdcharacter-icu63.so')+':'+str(component/'lib/libsdhost29.so')+':'+str(component/'lib/libdl_bio.so.0'),BIONIC_LD_LIBRARY_PATH=str(native),BIONIC_TRANSLATION_CONFIG_DIR=str(cfg),ANDROID_ROOT=str(component),ANDROID_DATA=str(data),SAILDROID_DATA_DIR=str(data),SD_BUILD_PROP=str(component/'build.prop'),ANDROID_RUNTIME_ROOT=str(component/'apex/com.android.runtime.debug'),ANDROID_TZDATA_ROOT=str(component/'apex/com.android.tzdata'),ICU_DATA=str(component/'usr/icu'),SAILDROID_ANDROID_LOG_STDERR='1')
def command(owner,data,main,args,props=(),debug=False):
 return [str(bridge/'private-userdb-exec'),str(owner),str(data),*([str(policy)]if owner!=10050 else[]),str(clone/'bin/dalvikvm'),'-XXlib:'+str(art_candidate),'-Xnoimage-dex2oat','-Ximage:'+str(component/'system/framework/boot.art'),'-Xbootclasspath:'+':'.join(map(str,paths)),'-Xbootclasspath-locations:'+':'.join(locations),'-Djava.library.path='+str(component/'lib')+':/var/tmp/saidroid-actual-phone-openjdk-20261031:'+str(platform/'lib64')+':'+str(platform/'apex/com.android.conscrypt/lib64')+':'+str(clone/'crypto')+':'+str(clone/'icu')+':'+str(clone/'artlib')+':'+str(clone/'homeart'),'-Dsaidroid.bridge.library='+str(bridge/'libsdbridge.so'),'-Dsaidroid.native.root='+str(platform),'-Xhidden-api-policy:disabled',*(['-Xcompiler-option','--debuggable']if debug else []),*props,'-cp',str(work/'empty.jar'),main,*args]
buspath=work/'bus';busready=work/'mce-ready'
policy=work/'app-policy-exec';policy_source=repo/'native/host/tests/app-filesystem-policy-exec.cpp';subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(policy_source),'-o',str(policy)],check=True);policy.chmod(0o555)
result['actual_kernel_policy_sha256']=sha(repo/'native/host/app-filesystem-policy.hpp')
result['actual_fixture_bridge']=dict(path=str(bridge/'libsdbridge.so'),sha256=sha(bridge/'libsdbridge.so'),scope='Explicit VM Binder/keystore bootstrap fixture, differs from production JNI bridge')
result['current_component_preload']={str(component/'lib'/n):sha(component/'lib'/n)for n in ['libsdhost29.so','libdl_bio.so.0']}
result['original_heap_options_unchanged']=True
result['actual_network_namespace']=os.readlink('/proc/self/ns/net')
cts_directory_state={};private_data=work/'data-root';private_data.mkdir(mode=0o755);subprocess.run(['mount','--bind',str(private_data),'/data'],check=True)
sys.path.insert(0,str(repo/'scripts/cts'));from temporary_directory_preparer import prepare_directories,cleanup_directories
def wait_fixture(path,p):
 for _ in range(160):
  if path.exists():return
  assert p.poll()is None,'Private bus fixture exited';time.sleep(.025)
 raise TimeoutError(str(path))
try:
 # Only the bus daemon gets this private NSS mount; original app launchers keep
 # their actual pre-existing per-UID account namespace implementation unchanged.
 passwd=work/'passwd';groups=work/'group';passwd.write_text(Path('/etc/passwd').read_text()+'\nfixture_keystore194:x:10050:10050:VM-only fixture:/nonexistent:/bin/false\n');groups.write_text(Path('/etc/group').read_text()+'\nfixture_keystore194:x:10050:\n');passwd.chmod(0o444);groups.chmod(0o444)
 config_bus=work/'bus.conf';config_bus.write_text('<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd"><busconfig><type>session</type><listen>unix:path='+str(buspath)+'</listen><auth>EXTERNAL</auth><policy context="default"><allow user="*"/><allow own="*"/><allow send_destination="*"/><allow receive_sender="*"/></policy></busconfig>')
 with(work/'bus.log').open('w')as log:bus=subprocess.Popen(['unshare','--mount','--','/usr/bin/python3',str(base/'run-keystore194-private-bus-v1-vm.py'),str(passwd),str(groups),str(config_bus)],stdout=log,stderr=log)
 processes.append(bus);wait_fixture(buspath,bus);mce_state=work/'mce-state';mce_state.write_text('unlocked\n');mce_state.chmod(0o444)
 with(work/'mce.log').open('w')as log:mce=subprocess.Popen(['/usr/bin/python3',str(base/'mce-lock-state194-service-fixture.py'),'unix:path='+str(buspath),str(mce_state),str(busready),'s'],stdout=log,stderr=log)
 processes.append(mce);wait_fixture(busready,mce);result['simulated_trusted_lock_state_fixture']=json.loads(busready.read_text());assert result['simulated_trusted_lock_state_fixture']['uid']==0
 space=os.statvfs(work);result['vm_space_after_fixture']=dict(blocksize=space.f_frsize,free_blocks=space.f_bfree,available_blocks=space.f_bavail);assert space.f_bavail*space.f_frsize>200000000,'Bounded ordinary-user VM space required before original launch'
 data=directory('verifier-data',65534);verify=json.loads((base/'verified-apk-identity193-contract-v9.json').read_text());assert verify['passed'];verify_command=verify['command']+[str(apk)]
 verifier_jar=Path('/var/tmp/saidroid-verified-apk-identity193-v9/verifier.jar');assert sha(verifier_jar)==verify['verifier_jar_sha256']
 verify_paths=[component/n for n in runtime['boot_jars']]+[verifier_jar,component/'lib/runtime.jar']
 verify_locations=['/home/art/api29-root/'+n for n in runtime['boot_jars']]+[str(verifier_jar),str(component/'lib/runtime.jar')]
 for i,arg in enumerate(verify_command):
  if arg.startswith('-XXlib:'):verify_command[i]='-XXlib:'+str(art_candidate)
  elif arg.startswith('-Ximage:'):verify_command[i]='-Ximage:'+str(component/'system/framework/boot.art')
  elif arg.startswith('-Xbootclasspath:'):verify_command[i]='-Xbootclasspath:'+':'.join(map(str,verify_paths))
  elif arg.startswith('-Xbootclasspath-locations:'):verify_command[i]='-Xbootclasspath-locations:'+':'.join(verify_locations)
  elif arg.startswith('-Djava.library.path='):verify_command[i]='-Djava.library.path='+str(component/'lib')+':'+arg.split('=',1)[1]
 result['actual_verifier_command']=verify_command
 def nobody():
  import resource
  resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.setgroups([]);os.setgid(65534);os.setuid(65534);os.umask(0o077)
 probe=subprocess.run([sys.executable,'-c','import os,sys;sys.exit(not os.access(sys.argv[1],os.R_OK))',str(apk)],preexec_fn=nobody,cwd=data);assert probe.returncode==0,'Original staged APK must be readable by verifier UID'
 p=subprocess.run(verify_command,env=env(65534,data),preexec_fn=nobody,cwd=data,capture_output=True,text=True,timeout=35);(work/'verification.stdout').write_text(p.stdout);(work/'verification.stderr').write_text(p.stderr);assert p.returncode==0,p.stderr[-5000:];identity=json.loads(next(l for l in reversed(p.stdout.splitlines())if l.startswith('VERIFIED_APK_IDENTITY=')).split('=',1)[1]);assert identity['apk_sha256']==sha(apk)and identity['package']=='android.libcore.cts'and identity['shared_user_id']is None;result['actual_verified_identity']=identity
 tools=Path('/var/tmp/saidroid-verified-apk-identity193-v9');subprocess.run([str(tools/'identity-tool'),str(identities),'init'],check=True,capture_output=True);assigned=json.loads(subprocess.check_output([str(tools/'identity-tool'),str(identities),'allocate',identity['package'],*identity['signers']],text=True));uid=assigned['uid'];result['actual_assignment']=assigned;result['identity_snapshot']=json.loads((identities/'identities.json').read_text())if(identities/'identities.json').is_file()else None
 apps=facade/'apps';apps.mkdir();install=apps/identity['package'];install.mkdir();shutil.copyfile(apk,install/'app.apk');(install/'app.apk').chmod(0o444);nativelibs=install/'lib';nativelibs.mkdir();native_inputs={}
 with zipfile.ZipFile(apk)as archive:
  for name in archive.namelist():
   if name.startswith('lib/arm64-v8a/')and name.endswith('.so'):
    p=nativelibs/Path(name).name;p.write_bytes(archive.read(name));p.chmod(0o444);native_inputs[name]=sha(p)
 result['original_apk_native_files']=native_inputs
 appdata=install/'data';appdata.mkdir(mode=0o700);os.chown(appdata,uid,uid)
 for label in ['files','cache','code_cache','device-protected']:(appdata/label).mkdir(mode=0o700);os.chown(appdata/label,uid,uid)
 prepare_directories(phone_plan['directory_preparation'],cts_directory_state,uid,uid);result['directory_preparation']=cts_directory_state
 label=result_name;request=appdata/'files/request.json';request.write_text(json.dumps(dict(run_id=label,component=phone_plan['component'],arguments=arguments))+'\n');os.chown(request,uid,uid);request.chmod(0o600);result['actual_request']=json.loads(request.read_text());serverdata=directory('server-data',10050);ready=serverdata/'ready';stop=serverdata/'stop';mapfile=serverdata/'native-maps';serverlog=work/'server.log'
 servercmd=command(10050,serverdata,'CombinedKeystoreServer',[str(device),str(built/'libsoftware-keystore.so'),str(keyfd),str(uid),'/var/tmp/saidroid-softkeymaster194-v5/abi-size.so',str(component/'lib/libdl_bio.so.0'),str(native/'libsoftkeymasterdevice.so'),str(ready),str(stop),str(mapfile),str(buspath),str(apk),apk_metadata['sha256']])
 with serverlog.open('w')as log:
  server=subprocess.Popen(servercmd,env=env(10050,serverdata),cwd=serverdata,stdout=log,stderr=log,pass_fds=(keyfd,));processes.append(server)
  for _ in range(160):
   if ready.exists()or server.poll()is not None:break
   time.sleep(.05)
  result['server_preflight_diagnostics']=dict(pid=server.pid,exit=server.poll(),ready=ready.exists(),log_bytes=serverlog.stat().st_size)
  if server.poll()is None:
   for n in ['stat','wchan','status']:
    try:result['server_preflight_diagnostics'][n]=(Path('/proc')/str(server.pid)/n).read_text()
    except OSError:pass
  assert ready.is_file()and server.poll()is None,serverlog.read_text(errors='replace')[-7000:]
  maps=mapfile.read_text();(work/'backend-native-maps.txt').write_text(maps);mapped={line.split()[-1]for line in maps.splitlines()if len(line.split())>=6 and line.split()[-1].startswith('/')};assert str(native/'libsoftkeymasterdevice.so')in mapped
  assert {p for p in mapped if p.endswith('/libart.so')}=={str(art_candidate)}
  assert 'KEYSTORE_FIXTURE_NATIVE_PATH=registered|'in serverlog.read_text(errors='replace')
  assert {p for p in mapped if p.endswith('/libdl_bio.so.0')}=={str(component/'lib/libdl_bio.so.0')},'Single current translated loader must be mapped'
  assert str(component/'lib/libsdhost29.so')in mapped,'Current host shim must be mapped in service too'
  result['actual_fixture_native_paths_appended']=True;result['actual_fixture_jar_sha256']=fixture_meta['jar_sha256']
  result['actual_server_art']=dict(path=str(art_candidate),sha256=sha(art_candidate));result['actual_server_boot_images']=sorted(p for p in mapped if p.endswith('.art'));assert result['actual_server_boot_images'];actual={};glibc_art_support={}
  for path in mapped:
   p=Path(path)
   if p.name in crypto['original_library_closure']:
    digest=sha(p)
    if digest==crypto['original_library_closure'][p.name]['sha256']:actual[path]=digest
    else:
     dynamic=subprocess.check_output(['readelf','-d',str(p)],text=True)
     assert p.parent==clone/'artlib'and p.name in['libbase.so','libcutils.so','liblog.so']and'libc.so.6'in dynamic and'[libc.so]'not in dynamic,'Unexpected non-original Bionic dependency'
     glibc_art_support[path]=dict(sha256=digest,dynamic=dynamic,scope='Separate glibc ART support library, not the same-name Bionic Keymaster dependency')
  assert len(actual)==len(crypto['original_library_closure']);result['actual_backend_native_mappings']=actual;result['separate_glibc_art_support']=glibc_art_support
  data=directory('client-runtime',uid);prefix='/home/art/apps/'+identity['package'];props=['-Dsaidroid.package='+identity['package'],'-Dsaidroid.apk='+prefix+'/app.apk','-Dsaidroid.native='+prefix+'/lib','-Dsaidroid.data='+prefix+'/data','-Dsaidroid.package.debuggable='+str(identity['debuggable']).lower(),'-Dsaidroid.instrumentation.request='+prefix+'/data/files/request.json'];props.append('-Ddexmaker.dexcache='+prefix+'/data/code_cache/dexmaker');props+=[];clientlog=work/'instrumentation.log';cmd=command(uid,data,'KeystoreInstrumentationBootstrap',[str(device)],props,identity['debuggable']);result['actual_client_command']=cmd
  with clientlog.open('w')as output:
   client=subprocess.Popen(cmd,env=env(uid,data),cwd='/',stdout=output,stderr=output,preexec_fn=lambda:__import__('resource').setrlimit(__import__('resource').RLIMIT_CORE,(0,0)));processes.append(client);finish=appdata/'files/instrumentation'/label/'result.json';deadline=time.monotonic()+12000;client_maps=None
   while time.monotonic()<deadline:
    if client_maps is None and client.poll()is None:
     try:
      rawmaps=Path('/proc')/str(client.pid)/'maps';maptext=rawmaps.read_text();mapped_client={line.split()[-1]for line in maptext.splitlines()if len(line.split())>=6 and line.split()[-1].startswith('/')};expected_images={str(component/'system/framework'/n)for n in json.loads((component/'share/build/boot-image-manifest.json').read_text())if n.endswith('.art')}
      if {p for p in mapped_client if p.endswith('.art')}==expected_images and any(p.endswith('/libjavacore.so')for p in mapped_client):
       (work/'client-preassert-maps.txt').write_text(maptext);result['client_preassert_native_maps']=sorted(p for p in mapped_client if p.endswith(('/libart.so','/libjavacore.so','/libsdhost29.so','/libdl_bio.so.0')))
       assert {p for p in mapped_client if p.endswith('/libart.so')}=={str(art_candidate)}and {p for p in mapped_client if p.endswith('/libjavacore.so')}=={str(component/'lib/libjavacore.so')}
       expected_native={str(component/'lib'/n)for n in ['libsdhost29.so','libdl_bio.so.0']}
       assert expected_native.issubset(mapped_client),'Current candidate native helpers must actually be mapped'
       assert str(bridge/'readable-native/libsdhost29.so')not in mapped_client,'Old fixture host shim must not be mapped'
       client_maps={p:sha(Path(p))for p in expected_images|{str(art_candidate),str(component/'lib/libjavacore.so')}|expected_native};(work/'client-runtime-maps.txt').write_text(maptext);result['actual_client_runtime_maps']=client_maps
     except FileNotFoundError:pass
    if finish.is_file()or client.poll()is not None:break
    if int(time.monotonic())%30==0:
     (work/'progress.json').write_text(json.dumps(dict(scope='Actual whole original MainLibcore VM progress, not acceptance',run=label,client_pid=client.pid,seconds_remaining=round(deadline-time.monotonic(),1),actual_maps_captured=bool(client_maps)),indent=2)+'\n')
    time.sleep(.5)
   result['actual_finish_exists']=finish.is_file()
   if not finish.is_file():
    event_file=finish.parent/'events.jsonl';partial=[]
    if event_file.is_file():
     (work/'instrumentation-events.jsonl').write_bytes(event_file.read_bytes())
     for rawline in event_file.read_text().splitlines():
      try:partial.append(json.loads(rawline))
      except ValueError:pass
    result['events']=partial;result['counts']=dict(collections.Counter({1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'}.get(e['code'],'other')for e in partial if e.get('event')=='status'and e.get('bundle',{}).get('test')));result['complete']=False;result['actual_client_exit']=client.poll()
    raise RuntimeError('Whole original MainLibcore native/process exit or original total timeout; raw partial events retained; '+clientlog.read_text(errors='replace')[-3000:])
   client.wait(timeout=10);assert client_maps and client.returncode==0,clientlog.read_text(errors='replace')[-8000:]
   result['instrumentation']=json.loads(finish.read_text());events=[json.loads(l)for l in(finish.parent/'events.jsonl').read_text().splitlines()];(work/'instrumentation-events.jsonl').write_bytes((finish.parent/'events.jsonl').read_bytes());result['events']=events;counts=collections.Counter();terminal=[]
   for event in events:
    b=event.get('bundle',{})
    if event.get('event')=='status'and b.get('test'):
     code=event['code'];counts[{1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'}.get(code,'other')]+=1
     if code!=1:terminal.append(dict(test=b.get('class','')+'#'+b['test'],code=code,stack=b.get('stack','')))
   result['counts']=dict(counts);result['terminal']=terminal;result['complete']=result['instrumentation']['code']==-1 and counts['started']==len(terminal)and counts['started']==79 and len({e['bundle']['numtests']for e in events if e.get('event')=='status'and'numtests'in e.get('bundle',{})})==1 and counts['started']==next(e['bundle']['numtests']for e in events if e.get('event')=='status'and'numtests'in e.get('bundle',{}));assert result['complete'];result['runner_reporting_fatal']='Fatal exception' in str(result['instrumentation'].get('results',{}));result['passed']=not(counts['failed']or counts['error']or result['runner_reporting_fatal']);text=clientlog.read_text(errors='replace');assert'KEYSTORE_ORIGINAL_BOOTSTRAP=running|'in text and'before_apk_classloader=true'in text
  stop.write_text('original declared instrumentation completed\n');server.wait(timeout=8);assert server.returncode==0,serverlog.read_text(errors='replace')[-7000:]
 result['original_inputs_unchanged']=sha(apk)==apk_metadata['sha256']and sha(config)==module['config_sha256'];assert result['original_inputs_unchanged']
except BaseException as e:result['error']=repr(e);result['traceback']=__import__('traceback').format_exc()
finally:
 os.close(keyfd)
 for p in reversed(processes):
  if p.poll()is None:
   p.terminate()
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
 if buspath.exists():buspath.unlink()
 if device.exists():device.unlink()
 assert all(p.poll()is not None for p in processes);cleanup_directories(cts_directory_state);result['original_directory_cleanup']=cts_directory_state
 subprocess.run(['umount','/data'],check=True);shutil.rmtree(private_data);result['private_data_mount_removed']=not private_data.exists()
 subprocess.run(['umount',str(mount)],check=True);mount.rmdir();subprocess.run(['umount','/home/art'],check=True);subprocess.run(['umount','/home'],check=True)
 for p in folders:shutil.rmtree(p)
 shutil.rmtree(facade);shutil.rmtree(key_state);shutil.rmtree(identities);apk.unlink();result['private_state_and_apk_removed']=not key_state.exists()and not identities.exists()and not facade.exists()and not apk.exists();result['owned_processes_reaped']=all(p.poll()is not None for p in processes);result['binderfs_removed']=not mount.exists();result['private_bus_removed']=not buspath.exists();(base/(result_name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in['events','terminal','original_library_closure','actual_client_command']},indent=2),flush=True)
assert result.get('complete')and result['private_state_and_apk_removed']and result['owned_processes_reaped']and result['binderfs_removed']
