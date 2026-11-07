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
os.umask(0o022);repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/cts-frame-repair-20261031';root=Path('/var/tmp/saidroid-java-cli282-headless-path-prototype-v4/root');work=Path('/var/tmp/saidroid-java-cli282-crypto-after-v4');assert not work.exists();work.mkdir();data=work/'private';data.mkdir(mode=0o700);os.chown(data,65534,65534);(data/'dalvik-cache').mkdir(mode=0o700);os.chown(data/'dalvik-cache',65534,65534);java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');inputs=repo/'build/codex-api29/inputs';classes=work/'classes';classes.mkdir();framework=inputs/'android-all-10-robolectric-5803371.jar';source=b/'JavaCli282CryptoMain.java'
subprocess.run([str(java/'javac'),'-source','8','-target','8','-nowarn','-bootclasspath','/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-oj-classes.jar:/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-libart-classes.jar:'+str(framework),'-d',str(classes),str(source)],check=True)
jar=work/'contract.jar';subprocess.run([str(java/'java'),'-cp',str(inputs/'r8-8.3.37.jar'),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(framework),'--output',str(jar),str(classes/'JavaCli282CryptoMain.class')],check=True);jar.chmod(0o444)
def nobody():
 import resource
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.setgroups([]);os.setgid(65534);os.setuid(65534);os.umask(0o077)
env=dict(PATH='/usr/bin:/bin',HOME=str(data),TMPDIR=str(data),ANDROID_DATA=str(data),SAILDROID_DATA_DIR=str(data),LANG='C.UTF-8');results=[]
for operation in ['digest','random','aes','rsa','tls']:
 cmd=[str(root/'bin/dalvikvm'),'-cp',str(jar),'JavaCli282CryptoMain',operation];p=subprocess.run(cmd,env=env,cwd=data,preexec_fn=nobody,text=True,capture_output=True,timeout=35);(work/(operation+'.stdout')).write_text(p.stdout);(work/(operation+'.stderr')).write_text(p.stderr);results.append(dict(operation=operation,command=cmd,code=p.returncode,stdout=p.stdout,stderr=p.stderr))
record=dict(scope='Diagnostic actual ordinaryCLI productionentry withpureJava crypto APIs; no injectedbootstrap/nativecalls/APK/originalCTS changes. VM only duringphonefullOJ; failures retained.',results=results,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),component_manifest_sha256=hashlib.sha256((root/'install-manifest.json').read_bytes()).hexdigest(),jar_sha256=hashlib.sha256(jar.read_bytes()).hexdigest(),all_operations_passed=all(v['code']==0 and'JAVA_CLI282_CRYPTO=PASS|operation='+v['operation']in v['stdout']for v in results));out=b/'java-cli282-crypto-after-v4.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
