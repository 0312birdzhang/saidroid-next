"""VM-only full boot AOT experiment; reads exact accepted J2 inputs, never installs."""
from pathlib import Path
import hashlib,json,os,subprocess,time,resource,shutil,signal
p=Path(__file__).parent;d=p/'distribution-v7';root=d/'assembly/root';out=p/'full-boot-preloaded-v1';scratch=Path('/var/tmp/saidroid-full-boot-preloaded-v1');assert not out.exists()and not scratch.exists();out.mkdir();scratch.mkdir();(scratch/'arm64').mkdir();(scratch/'data').mkdir()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();manifest=json.loads((d/'distribution-manifest.json').read_text());assert sha(d/'distribution-manifest.json')=='8e0f8042fbcbf9e3738ad9d5690d31702568267182182236de71ec0c3d06362a'
config=json.loads((root/'runtime.json').read_text());jars=config['boot_jars']+['lib/runtime.jar'];assert len(jars)==15
inputs={}
for name in jars+['runtime.json','build.prop']+[key for key in manifest['files']if key.startswith('compiler/')]:
 f=root/name;expected=manifest['files'][name];assert sha(f)==expected['sha256'];inputs[name]=dict(sha256=sha(f),bytes=f.stat().st_size)
empty=scratch/'image-classes.txt';shutil.copyfile(root/'system/etc/preloaded-classes',empty);shutil.copyfile(empty,out/'image-classes.txt');inputs['system/etc/preloaded-classes']=dict(sha256=sha(empty),bytes=empty.stat().st_size);compiler=root/'compiler/bin/dex2oat'
with(out/'compiler-help.log').open('wb')as log:subprocess.run([str(compiler),'--help'],stdout=log,stderr=subprocess.STDOUT,timeout=15)
command=[str(compiler),'--host','--instruction-set=arm64','--base=0x70000000','--compiler-filter=speed','-j2','--runtime-arg','-Xmx1536m','--image='+str(scratch/'arm64/boot.art'),'--oat-file='+str(scratch/'arm64/boot.oat'),'--image-classes='+str(empty),'--runtime-arg','-Xbootclasspath:'+':'.join(str(root/name)for name in jars),'--runtime-arg','-Xbootclasspath-locations:'+':'.join('/home/art/api29-root/'+name for name in jars)]
for name in jars:command+=['--dex-file='+str(root/name),'--dex-location=/home/art/api29-root/'+name]
env=dict(os.environ,ANDROID_ROOT=str(root),ANDROID_DATA=str(scratch/'data'),SD_BUILD_PROP=str(root/'build.prop'));recipe=dict(scope='VM-only nonempty exact packaged AOSP preloaded-classes boot image experiment; no target install, runtime modification or performance claim',command=command,inputs=inputs,compiler_manifest_sha256=sha(root/'compiler/manifest.json'),jars=jars,logical_locations=['/home/art/api29-root/'+name for name in jars],threads=2,heap_limit_mb=1536,rss_limit_mb=4096,timeout_seconds=1200,minimum_available_mb=768,scratch=str(scratch))
(out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');start=time.monotonic();samples=[];reason=None
with(out/'build.log').open('wb')as log:
 child=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 (out/'pid.json').write_text(json.dumps(dict(pid=child.pid,parent=os.getpid())))
 while child.poll()is None:
  try:
   status=(Path('/proc')/str(child.pid)/'status').read_text();rss=next(int(line.split()[1])for line in status.splitlines()if line.startswith('VmRSS:'));memory=Path('/proc/meminfo').read_text();available=next(int(line.split()[1])for line in memory.splitlines()if line.startswith('MemAvailable:'));samples.append(dict(seconds=time.monotonic()-start,rss_kib=rss,mem_available_kib=available))
   if rss>4*1024*1024:reason='RSS exceeded 4096 MiB'
   if available<768*1024:reason='VM available memory fell below 768 MiB'
  except(FileNotFoundError,StopIteration):pass
  if time.monotonic()-start>1200:reason='1200-second deadline'
  if reason:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
   break
  time.sleep(1)
code=child.wait();files={};unchanged=all(sha(root/name)==item['sha256']for name,item in inputs.items())
for f in sorted((scratch/'arm64').iterdir()):
 if f.is_file():files[f.name]=dict(bytes=f.stat().st_size,sha256=sha(f))
passed=code==0 and unchanged and len(files)==45 and all(item['bytes']>0 for item in files.values())
if passed:shutil.copytree(scratch/'arm64',out/'arm64')
usage=resource.getrusage(resource.RUSAGE_CHILDREN);result=dict(passed=passed,returncode=code,reason=reason,seconds=time.monotonic()-start,inputs_unchanged=unchanged,files=files,samples=samples,child_cpu_seconds=usage.ru_utime+usage.ru_stime,child_max_rss_kib=usage.ru_maxrss,source_manifest_sha256=sha(d/'distribution-manifest.json'),runtime_acceptance='not-tested',performance_acceptance='not-tested',device_accessed=False)
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['samples','files']}),flush=True)
raise SystemExit(0 if passed else 1)
