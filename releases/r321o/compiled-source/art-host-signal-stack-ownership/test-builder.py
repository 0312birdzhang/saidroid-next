from pathlib import Path
import hashlib,json,os,resource,subprocess,traceback
os.umask(0o022)
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-signal-stack291-20261102-v1'
work=Path('/var/tmp/saidroid-stack291-contract-v5');work.mkdir(mode=0o755)
old=Path('/var/tmp/saidroid-art220-signal-stack-contract-v1');clone=Path('/var/tmp/saidroid-unprivileged182-runtime-20261031')
component=Path('/var/tmp/saidroid-xml-factory218-v1-formal-vm-component/root');java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');inputs=repo/'build/codex-api29/inputs';src=repo/'scripts/api29/tests/signal-stack-ownership';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((b/'art-build.json').read_text())['passed']
classes=work/'classes';classes.mkdir()
subprocess.run(['gcc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(src/'unmap-observer.c'),'-o',str(work/'observer.so')],check=True)
subprocess.run(['gcc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-pthread','-I'+str(java.parent/'include'),'-I'+str(java.parent/'include/linux'),str(src/'ownership.c'),'-o',str(work/'helper.so'),'-ldl'],check=True)
subprocess.run([str(java/'javac'),'--release','8','-d',str(classes),str(src/'ArtSignalStackOwnership.java')],check=True)
subprocess.run([str(java/'java'),'-cp',str(inputs/'r8-8.3.37.jar'),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(inputs/'android-all-10-robolectric-5803371.jar'),'--output',str(work/'runner.jar'),str(classes/'ArtSignalStackOwnership.class')],check=True)
data=work/'data';data.mkdir(mode=0o700);os.chown(data,65534,65534)
for n in ['home','tmp','dalvik-cache','config']:
 p=data/n;p.mkdir(mode=0o700);os.chown(p,65534,65534)
config=data/'config/runtime.cfg';config.write_text('libc.so libc_bio.so.0\nlibstdc++.so libstdc++_bio.so.0\nlibm.so libm.so.6\nlibdl.so libdl.so.2\n');os.chown(config,65534,65534)
runtime=json.loads((component/'runtime.json').read_text());paths=[old/'encoded'/n for n in runtime['boot_jars']]+[work/'runner.jar'];locations=['/home/art/api29-root/'+n for n in runtime['boot_jars']]+[str(work/'runner.jar')]
prefix=str(old/'native')+':'+str(component/'lib')+':'+str(clone/'icu')+':'+str(clone/'artlib')
env=dict(PATH='/usr/bin:/bin',HOME=str(data/'home'),TMPDIR=str(data/'tmp'),LANG='C.UTF-8',ANDROID_ROOT=str(old/'androidroot'),ANDROID_DATA=str(data),BIONIC_TRANSLATION_CONFIG_DIR=str(data/'config'),ICU_DATA=str(clone/'bionic-icu'),
 LD_LIBRARY_PATH='/var/tmp/saidroid-actual-phone-openjdk-20261031:'+str(clone/'crypto')+':'+prefix+':'+str(clone/'patched')+':'+str(old/'linker')+':'+str(clone/'homeart')+':/usr/local/lib',
 LD_PRELOAD=str(work/'observer.so')+':/var/tmp/saidroid-fdlibm-native-20261031-r188-v4/libsdstrictmath-fdlibm.so:/var/tmp/saidroid-character-native-20261031-r189-v2/libsdcharacter-icu63.so:/var/tmp/saidroid-fdsan219-registry-lock-v1/libsdhost29.so:'+str(old/'linker/libdl_bio.so.0'))
def nobody():
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.setgroups([]);os.setgid(65534);os.setuid(65534);os.umask(0o077)
rows=[]
try:
 for label,art,modes in [('before',Path('/var/tmp/saidroid-art240-host-math-precision-v1/libart.so'),[0,2]),('after',Path('/var/tmp/saidroid-art291-host-signal-stack-ownership-v1/libart.so'),range(5))]:
  for mode in modes:
   readable=work/label;readable.mkdir(exist_ok=True);private_art=readable/'libart.so';private_art.write_bytes(art.read_bytes());private_art.chmod(0o444);assert sha(private_art)==sha(art);art=private_art
   cmd=[str(clone/'bin/dalvikvm'),'-XXlib:'+str(art),'-Xnoimage-dex2oat','-Ximage:'+str(old/'boot/boot.art'),'-Xbootclasspath:'+':'.join(map(str,paths)),'-Xbootclasspath-locations:'+':'.join(locations),'-Djava.library.path='+prefix+':/var/tmp/saidroid-actual-phone-openjdk-20261031','-Dstack.art='+str(art),'-Dstack.helper='+str(work/'helper.so'),'-cp',str(work/'empty.jar'),'ArtSignalStackOwnership',str(mode)]
   p=subprocess.run(cmd,env=env,preexec_fn=nobody,cwd=data,capture_output=True,text=True,timeout=180)
   (b/('v5-'+label+'-'+str(mode)+'.stdout')).write_text(p.stdout);(b/('v5-'+label+'-'+str(mode)+'.stderr')).write_text(p.stderr)
   expected_failure=label=='before'and mode==2
   ok=(p.returncode!=0 and 'munmap(allocated_signal_stack' in p.stderr)if expected_failure else(p.returncode==0 and 'ART_STACK_OWNERSHIP=PASS|mode='+str(mode)+'|threads=64|'in p.stdout)
   row=dict(label=label,mode=mode,returncode=p.returncode,expected_failure=expected_failure,passed=ok,art_sha256=sha(art));rows.append(row);print(json.dumps(row),flush=True)
   assert ok,p.stdout[-2000:]+p.stderr[-4000:]
finally:
 result=dict(passed=len(rows)==7 and all(r['passed']for r in rows),scope='Actual ART JNI attach/detach, UID65534, baseline foreign-stack failure isolated in VM; five candidate modes normal/disabled/foreign/prior/owned-alias, each64threads with real guards, exact successful munmap observed at actual kernel boundary plus immediate mincore ENOMEM, foreign content retention; observer changes no syscall arguments/results. No phone/CTS claim.',rows=rows,sources={str(p.relative_to(repo)):sha(p)for p in src.iterdir()if p.is_file()})
 (b/'ownership-contract-v5.json').write_text(json.dumps(result,indent=2)+'\n')
