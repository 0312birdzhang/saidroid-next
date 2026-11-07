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
os.umask(0o022);repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/cts-frame-repair-20261031';root=Path('/var/tmp/saidroid-java-cli268-prototype-v4/root');work=Path('/var/tmp/saidroid-java-cli268-policy-contract-v1');assert not work.exists();work.mkdir();data=work/'private';data.mkdir(mode=0o700);os.chown(data,65534,65534);(data/'dalvik-cache').mkdir(mode=0o700);os.chown(data/'dalvik-cache',65534,65534);java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');inputs=repo/'build/codex-api29/inputs';classes=work/'classes';classes.mkdir();framework=inputs/'android-all-10-robolectric-5803371.jar';source=b/'JavaCli268ContractMain.java'
sources=[b/'JavaCli268ReturnMain.java',b/'JavaCli268ThrowMain.java'];subprocess.run([str(java/'javac'),'--release','8','-nowarn','-cp',str(framework),'-d',str(classes),*map(str,sources)],check=True)
jar=work/'contract.jar';subprocess.run([str(java/'java'),'-cp',str(inputs/'r8-8.3.37.jar'),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(framework),'--output',str(jar),*map(str,classes.glob('*.class'))],check=True);jar.chmod(0o444)
def nobody():
 import resource
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.setgroups([]);os.setgid(65534);os.setuid(65534);os.umask(0o077)
env=dict(PATH=str(root/'bin')+':/usr/bin:/bin',HOME=str(data),TMPDIR=str(data),ANDROID_DATA=str(data),SAILDROID_DATA_DIR=str(data),LANG='C.UTF-8');rows=[]
def execute(label,args,expected,marker=None,ordinary=True,executable=None):
 cmd=[str(executable or root/'bin/dalvikvm'),*args];p=subprocess.run(cmd,env=env,cwd=data,preexec_fn=nobody if ordinary else None,text=True,capture_output=True,timeout=35);(work/(label+'.stdout')).write_text(p.stdout);(work/(label+'.stderr')).write_text(p.stderr);assert p.returncode==expected,(label,p.returncode,p.stdout,p.stderr)
 if marker:assert marker in p.stdout+p.stderr,(label,p.stdout,p.stderr)
 rows.append(dict(label=label,returncode=p.returncode,stdout_sha256=hashlib.sha256(p.stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr.encode()).hexdigest(),command=cmd))
execute('normal-return',['-cp',str(jar),'JavaCli268ReturnMain','argument-preserved'],0,'JAVA_CLI268_RETURN=PASS')
execute('real-java-exception',['-cp',str(jar),'JavaCli268ThrowMain'],10,'ordinary-user-cli-exception')
execute('no-arguments',[],2,'Usage: dalvikvm')
execute('missing-classpath',['-cp'],125,'Classpath option needs a value')
execute('root-refused',[],125,'ordinary caller',ordinary=False)
for i,arg in enumerate(['-XXlib:/tmp/untrusted.so','-Ximage:/tmp/untrusted.art','-Xbootclasspath:/tmp/empty.jar','-Xbootclasspath/a:/tmp/empty.jar','-Xtarget-sdk-version:1','-Xhidden-api-policy:disabled','-agentpath:/tmp/untrusted.so','-agentlib:jdwp','-Xplugin:/tmp/untrusted.so','-Xrunjdwp:transport=dt_socket','-Xcompiler-option','-Ximage-compiler-option']):execute('reject-option-'+str(i),[arg,'-cp',str(jar),'JavaCli268ReturnMain','argument-preserved'],125,'cannot be overridden')
# A CLI executable copied into a caller-owned pseudo-component may not select it.
foreign=data/'foreign';foreign.mkdir(mode=0o700);os.chown(foreign,65534,65534);(foreign/'bin').mkdir(mode=0o700);os.chown(foreign/'bin',65534,65534);shutil.copyfile(root/'bin/dalvikvm',foreign/'bin/dalvikvm');(foreign/'bin/dalvikvm').chmod(0o755);os.chown(foreign/'bin/dalvikvm',65534,65534);execute('untrusted-component',[],125,'root is not root-owned',executable=foreign/'bin/dalvikvm')
record=dict(scope='Actual CLI VM startup return/uncaught exception/noargs/stdio and negative policy gates; private root copied by caller cannot selectruntime, no root/caps/agent/image/SDK/hiddenAPIoverride. No phone run.',passed=True,checks=len(rows),results=rows,source_sha256=hashlib.sha256((repo/'native/commands/java-cli/dalvikvm.cpp').read_bytes()).hexdigest(),bootstrap_source_sha256=hashlib.sha256((repo/'native/commands/java-cli/SdJavaCommand.java').read_bytes()).hexdigest());out=b/'java-cli268-policy-contract-v1.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
