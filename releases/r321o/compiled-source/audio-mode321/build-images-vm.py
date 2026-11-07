from pathlib import Path
import hashlib,json,os,subprocess,time,resource,shutil,signal,argparse
p=Path(__file__).resolve().parent;a=argparse.ArgumentParser();a.add_argument('variant',choices=['candidate']);variant=a.parse_args().variant;root=p.parent/'distribution-v14/assembly/root';candidate=p/'build-v2/candidate';out=p/(variant+'-images-v1')
assert str(p).startswith('/media/psf/Home/WorkSpace/saidroid-next/build/evidence/')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();build=json.loads((candidate/'result.json').read_text());assert build['passed']
assert sha(candidate/'encoded/lib/runtime.jar')==build['encoded_runtime_sha256']
out.mkdir();scratch=Path('/var/tmp/saidroid-audio-mode-images321-'+variant+'-v1');scratch.mkdir();(scratch/'arm64').mkdir();(scratch/'data').mkdir()
config=json.loads((root/'runtime.json').read_text());jars=config['boot_jars']+['lib/runtime.jar'];assert len(jars)==15
paths={name:(candidate/'encoded'/name if name=='lib/runtime.jar'else root/name)for name in jars}
inputs={name:sha(path)for name,path in paths.items()};empty=scratch/'image-classes.txt';empty.write_text('')
command=[str(root/'compiler/bin/dex2oat'),'--host','--instruction-set=arm64','--base=0x70000000','--compiler-filter=speed','-j2','--runtime-arg','-Xmx1536m','--image='+str(scratch/'arm64/boot.art'),'--oat-file='+str(scratch/'arm64/boot.oat'),'--image-classes='+str(empty),'--runtime-arg','-Xbootclasspath:'+':'.join(str(paths[name])for name in jars),'--runtime-arg','-Xbootclasspath-locations:'+':'.join('/home/art/api29-root/'+name for name in jars)]
for name in jars:command+=['--dex-file='+str(paths[name]),'--dex-location=/home/art/api29-root/'+name]
(out/'recipe.json').write_text(json.dumps(dict(command=command,inputs=inputs,scope='isolated VM candidate, no app cache reuse or promotion'),indent=2)+'\n')
env=dict(os.environ,ANDROID_ROOT=str(root),ANDROID_DATA=str(scratch/'data'),SD_BUILD_PROP=str(root/'build.prop'));start=time.monotonic();samples=[];reason=None
with(out/'build.log').open('wb')as log:
 child=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 while child.poll()is None:
  try:
   status=(Path('/proc')/str(child.pid)/'status').read_text();rss=next(int(line.split()[1])for line in status.splitlines()if line.startswith('VmRSS:'));available=next(int(line.split()[1])for line in Path('/proc/meminfo').read_text().splitlines()if line.startswith('MemAvailable:'))
   samples.append(dict(seconds=time.monotonic()-start,rss_kib=rss,available_kib=available))
   if rss>4*1024*1024 or available<768*1024:reason='VM memory guard'
  except(FileNotFoundError,StopIteration):pass
  if time.monotonic()-start>180:reason='compile deadline'
  if reason:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
   break
  time.sleep(1)
 rc=child.wait()
files={f.name:dict(sha256=sha(f),bytes=f.stat().st_size)for f in sorted((scratch/'arm64').iterdir())if f.is_file()}
unchanged=all(sha(path)==inputs[name]for name,path in paths.items());passed=rc==0 and len(files)==45 and unchanged
if passed:
 shutil.copytree(scratch/'arm64',out/'arm64')
 metadata=dict(schema='saildroid-isolated-audio-mode-images-v1',variant=variant,files=files,boot_jars=inputs,runtime_sha256=build['encoded_runtime_sha256'],compiler_filter='speed',source_scope='exact L6 + immutable Android audio-service-domain read getter',phone_accessed=False,app_caches_built=False)
 (out/'image-manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
 runtime=json.loads((root/'runtime.json').read_text());runtime['boot_image']['manifest_sha256']=sha(out/'image-manifest.json');runtime['hidden_api']['manifest_sha256']=sha(candidate/'encoded/manifest.json');runtime['isolated_candidate']['runtime_sha256']=build['encoded_runtime_sha256'];runtime['isolated_candidate']['image_manifest_sha256']=sha(out/'image-manifest.json');runtime['isolated_candidate']['hidden_api_manifest_sha256']=sha(candidate/'encoded/manifest.json');runtime['isolated_candidate']['variant']='audio-mode-readonly-v1';runtime['audio_mode_readonly']=dict(schema='saidroid-android-applied-audio-mode-readonly-v1',source='android-applied-mode',initialized_mode=0,supported_transitions='none',host_call_mode='unintegrated',setter='explicitly-unsupported',baseline_runtime_sha256=sha(root/'lib/runtime.jar'));(out/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
result=dict(passed=passed,returncode=rc,reason=reason,seconds=time.monotonic()-start,files=files,inputs_unchanged=unchanged,samples=samples,phone_accessed=False,accepted_root_changed=False,variant=variant,image_manifest_sha256=sha(out/'image-manifest.json')if passed else None,runtime_metadata_sha256=sha(out/'runtime.json')if passed else None,app_caches_built=False)
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ('files','samples')},indent=2));assert passed
