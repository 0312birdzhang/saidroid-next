from pathlib import Path
import os,json,hashlib,subprocess,shutil,sys
if '--inside'not in sys.argv:
 p=subprocess.run(['unshare','--mount','--',sys.executable,str(Path(__file__).resolve()),'--inside'],capture_output=True,text=True,timeout=90);print(p.stdout);print(p.stderr,file=sys.stderr);sys.exit(p.returncode)
subprocess.run(['mount','--make-rprivate','/'],check=True)
subprocess.run(['mount','-t','tmpfs','-o','mode=0755,size=4m,nr_inodes=128','tmpfs','/home'],check=True);Path('/home/art').mkdir(mode=0o755);Path('/home/art').chmod(0o755);lib=Path('/home/art/lib');lib.mkdir(mode=0o755);lib.chmod(0o755)
clone=Path('/var/tmp/saidroid-unprivileged182-runtime-20261031')
for directory in ['homeart','crypto','icu','artlib']:
 for p in(clone/directory).iterdir():
  target=lib/p.name
  if p.is_file()and not target.exists():target.symlink_to(p)
(lib/'libopenjdk.so').unlink();(lib/'libopenjdk.so').symlink_to('/var/tmp/saidroid-actual-phone-openjdk-20261031/libopenjdk.so')
os.umask(0o022);repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/cts-frame-repair-20261031';root=Path('/var/tmp/saidroid-java-cli282-headless-path-prototype-v4/root');work=Path('/var/tmp/saidroid-java-cli282-basic-contract-v2');assert not work.exists();work.mkdir();data=work/'private';data.mkdir(mode=0o700);os.chown(data,65534,65534);(data/'dalvik-cache').mkdir(mode=0o700);os.chown(data/'dalvik-cache',65534,65534);java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');inputs=repo/'build/codex-api29/inputs';classes=work/'classes';classes.mkdir();framework=inputs/'android-all-10-robolectric-5803371.jar';source=b/'JavaCli268ContractMain.java'
subprocess.run([str(java/'javac'),'-source','8','-target','8','-nowarn','-bootclasspath','/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-oj-classes.jar:/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-libart-classes.jar:'+str(framework),'-d',str(classes),str(source)],check=True)
jar=work/'contract.jar';subprocess.run([str(java/'java'),'-cp',str(inputs/'r8-8.3.37.jar'),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(framework),'--output',str(jar),str(classes/'JavaCli268ContractMain.class')],check=True);jar.chmod(0o444)
def nobody():
 import resource
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.setgroups([]);os.setgid(65534);os.setuid(65534);os.umask(0o077)
clone=Path('/var/tmp/saidroid-unprivileged182-runtime-20261031');env=dict(PATH='/usr/bin:/bin',HOME=str(data),TMPDIR=str(data),ANDROID_DATA=str(data),SAILDROID_DATA_DIR=str(data),LANG='C.UTF-8');cmd=[str(root/'bin/dalvikvm'),'-cp',str(jar),'JavaCli268ContractMain','hello space','中文',str(data)];p=subprocess.run(cmd,env=env,cwd=data,preexec_fn=nobody,input='stdin payload\n',text=True,capture_output=True,timeout=35);(work/'stdout').write_text(p.stdout);(work/'stderr').write_text(p.stderr);record=dict(scope='Actual component CLI VM test only; no phone. OrdinaryUID stdin/stdout/stderr/exit/args/fileIO/seccomp/native63/Math/actualART9images invariants.',returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,command=cmd,passed=p.returncode==23 and'JAVA_CLI268_CONTRACT=PASS|uid=65534|hidden_api=denied|images=9|'in p.stdout and'JAVA_CLI268_STDERR=actual-java'in p.stderr and'SD_JAVA_CLI=ready|sdk=29|hidden_api=enabled|user_loader=application|ui=false'in p.stderr,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest());(b/'java-cli282-basic-contract-v2.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));assert record['passed']
