from pathlib import Path
import os,json,hashlib,subprocess,shutil,sys
if '--inside'not in sys.argv:
 p=subprocess.run(['unshare','--mount','--net','--',sys.executable,str(Path(__file__).resolve()),'--inside'],capture_output=True,text=True,timeout=90);print(p.stdout);print(p.stderr,file=sys.stderr);sys.exit(p.returncode)
subprocess.run(['mount','--make-rprivate','/'],check=True)
subprocess.run(['mount','-t','tmpfs','-o','mode=0755,size=4m,nr_inodes=128','tmpfs','/home'],check=True);Path('/home/art').mkdir(mode=0o755);Path('/home/art').chmod(0o755);lib=Path('/home/art/lib');lib.mkdir(mode=0o755);lib.chmod(0o755)
clone=Path('/var/tmp/saidroid-unprivileged182-runtime-20261031')
for directory in ['homeart','crypto','icu','artlib']:
 for p in(clone/directory).iterdir():
  target=lib/p.name
  if p.is_file()and not target.exists():target.symlink_to(p)
(lib/'libopenjdk.so').unlink();(lib/'libopenjdk.so').symlink_to('/var/tmp/saidroid-actual-phone-openjdk-20261031/libopenjdk.so')
os.umask(0o022)
import socket,threading,time,resource,ctypes
subprocess.run(['ip','link','set','lo','up'],check=True)
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/cts-frame-repair-20261031';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();roots=dict(before=Path('/var/tmp/saidroid-java-cli282-headless-v1-formal-vm-component/root'),after=Path('/var/tmp/saidroid-icmp-cleanup286-prototype-v1/root'));work=Path('/var/tmp/saidroid-icmp-cleanup286-own-v1');assert not work.exists();work.mkdir();classes=work/'classes';classes.mkdir();data=work/'private';data.mkdir(mode=0o700);os.chown(data,65534,65534);(data/'dalvik-cache').mkdir(mode=0o700);os.chown(data/'dalvik-cache',65534,65534);java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');inputs=repo/'build/codex-api29/inputs';framework=inputs/'android-all-10-robolectric-5803371.jar';source=repo/'scripts/api29/tests/network/Network286ReachabilityContract.java';out=b/'icmp-cleanup286-own-v1.json';assert not out.exists();record=dict(passed=False,scope='Actual ordinaryCLI genuine ART/LinuxJNI/API29/zeroCap/noNewPriv/nineimages, private NET namespace only with no external route. Same literal addresses and native kernel permissions; before actual nullFD crashes under ICMP denial, after real TCP listener accepts32 fallback connects; allowed ICMP stays functional. No original CTS change or phone claim.',source_sha256=sha(source),module_manifest_sha256=sha(Path('/var/tmp/saidroid-icmp-cleanup286-module-v1/manifest.json')),prototype_proof_sha256=sha(b/'icmp-cleanup286-prototype-v1.json'),results=[])
def nobody():
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.setgroups([]);os.setgid(65534);os.setuid(65534);os.umask(0o077);assert ctypes.CDLL(None).prctl(38,1,0,0,0)==0
try:
 subprocess.run([str(java/'javac'),'-source','8','-target','8','-nowarn','-bootclasspath','/var/tmp/saidroid-icmp-cleanup286-module-v1/core-oj-classes.jar:/var/tmp/saidroid-classpath-cache-lifecycle263-module-v3/core-libart-classes.jar:'+str(framework),'-d',str(classes),str(source)],check=True)
 jar=work/'contract.jar';subprocess.run([str(java/'java'),'-cp',str(inputs/'r8-8.3.37.jar'),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(framework),'--output',str(jar),*map(str,classes.rglob('*.class'))],check=True);jar.chmod(0o444);record['jar_sha256']=sha(jar)
 env=dict(PATH='/usr/bin:/bin',HOME=str(data),TMPDIR=str(data),ANDROID_DATA=str(data),SAILDROID_DATA_DIR=str(data),LANG='C.UTF-8')
 for allowed in [True,False]:
  Path('/proc/sys/net/ipv4/ping_group_range').write_text('0 2147483647\n'if allowed else'1 0\n')
  for which,root in roots.items():
   listeners=[];accepted=[];finished=threading.Event();threads=[];server_errors=[]
   def accept(fd):
    try:
     while not finished.is_set():
      try:client,address=fd.accept();accepted.append(address);client.close()
      except socket.timeout:continue
    except BaseException as error:server_errors.append(repr(error))
   for family,endpoint in [(socket.AF_INET,('127.0.0.1',7)),(socket.AF_INET6,('::1',7))]:
    fd=socket.socket(family,socket.SOCK_STREAM);fd.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    if family==socket.AF_INET6:fd.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,1)
    fd.bind(endpoint);fd.listen(128);fd.settimeout(.1);listeners.append(fd);thread=threading.Thread(target=accept,args=(fd,));thread.start();threads.append(thread)
   label=which+('-icmp-allowed'if allowed else'-icmp-denied');cmd=[str(root/'bin/dalvikvm'),'-cp',str(jar),'Network286ReachabilityContract',label]
   try:p=subprocess.run(cmd,env=env,cwd=data,preexec_fn=nobody,text=True,capture_output=True,timeout=45)
   finally:
    finished.set()
    for thread in threads:thread.join(2);assert not thread.is_alive()
    for fd in listeners:fd.close()
   row=dict(label=label,allowed=allowed,which=which,component_manifest_sha256=sha(root/'install-manifest.json'),code=p.returncode,command=cmd,stdout=p.stdout,stderr=p.stderr,tcp_accepted=accepted,server_errors=server_errors);record['results'].append(row);(work/(label+'.stdout')).write_text(p.stdout);(work/(label+'.stderr')).write_text(p.stderr);assert p.returncode==0 and not server_errors,(label,p.stderr[-4000:]);lines=[line for line in p.stdout.splitlines()if line.startswith('NETWORK286_REACHABILITY=')];assert len(lines)==1;v=json.loads(lines[0].split('=',1)[1]);row['actual']=v;assert v['uid']==65534 and v['images']==9 and v['fd_after']<=v['fd_before']+1,v
   assert len(v['results'])==4 and sum(len(z['calls'])for z in v['results'])==34
   for index,z in enumerate(v['results']):
    assert (z.get('raw_socket_opened')is True)if allowed else(z.get('raw_socket_errno')==13),z
    for call in z['calls']:
     if not allowed and which=='before':assert call.get('error')=='java.lang.NullPointerException'and'isSocket$'in call['message'],call
     else:assert call.get('reachable')is(index<2)and'error'not in call,call
   assert len(accepted)==(32 if not allowed and which=='after'else 0),(label,accepted)
 record['passed']=True
finally:
 shutil.rmtree(data);record['private_data_removed']=not data.exists();out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(passed=record['passed'],private_data_removed=record['private_data_removed'],results=[dict(label=v['label'],code=v['code'],tcp_accept_count=len(v['tcp_accepted']),actual=v.get('actual'))for v in record['results']]),indent=2))
