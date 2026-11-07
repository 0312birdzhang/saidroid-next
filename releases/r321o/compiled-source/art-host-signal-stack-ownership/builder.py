from pathlib import Path
import os,fcntl,hashlib,json,subprocess,shutil,time,stat,traceback
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');b=repo/'build/evidence/qq-signal-stack291-20261102-v1';cts=repo/'build/evidence/cts-frame-repair-20261031';art=Path('/tmp/art-build/art-standalone');out=Path('/var/tmp/saidroid-art291-host-signal-stack-ownership-v1');out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lock=open('/var/lock/saidroid-art-host-math-build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.environ['JAVA_HOME']='/tmp/jdkfull/jdk-21.0.13+9';os.environ['PATH']=os.environ['JAVA_HOME']+'/bin:'+os.environ['PATH']
old=json.loads((cts/'art240-host-math-precision-v1-build.json').read_text());stack=json.loads((cts/'art220-host-signal-stack-v1-build.json').read_text());meta=json.loads((repo/'native/compat/art-host-signal-stack-ownership/sources.json').read_text());assert old['passed']and stack['passed'];assert sha(Path('/var/tmp/saidroid-art240-host-math-precision-v1/libart.so'))==old['binary_sha256']=='3f1f4df98fead04768503e0cd797a8ffde46c684bf5e5cba62dea12df3f2faf3'
expected={n:dict(base=v['base_sha256'],patched=v['patched_sha256'])for n,v in stack['sources'].items()};expected.update({n:dict(base=v['baseline_sha256'],patched=v['patched_sha256'])for n,v in old['sources'].items()});assert len(expected)==6
sources={n:((art/n).read_bytes(),(art/n).stat())for n in expected}
for n,v in expected.items():assert sha(art/n)==v['base'],n
assert sha(repo/meta['source'])==meta['source_sha256']and sha(repo/meta['patch'])==meta['patch_sha256']
inter=art/'out/host/linux-x86/obj/SHARED_LIBRARIES/libart_intermediates';files=[p for p in inter.rglob('*')if p.is_file()]+[art/'out/host/linux-x86/lib64/libart.so',art/'out/host/linux-x86/obj/lib/libart.so'];backups={};backup=b/'art-build-backups';backup.mkdir();record=dict(passed=False,scope=meta['scope'],started=time.time(),baseline_binary_sha256=old['binary_sha256']);started=time.monotonic()
for p in files:
 n=str(p.relative_to(art));t=backup/n;t.parent.mkdir(parents=True,exist_ok=True);s=p.stat();shutil.copyfile(p,t);t.chmod(stat.S_IMODE(s.st_mode));h=sha(p);assert sha(t)==h;backups[n]=dict(sha256=h,mtime_ns=s.st_mtime_ns,atime_ns=s.st_atime_ns,mode=stat.S_IMODE(s.st_mode))
(b/'backup-manifest.json').write_text(json.dumps(backups,indent=2)+'\n');print('ART291_BACKUP=ready|files='+str(len(backups)),flush=True)
def build(label):
 with(b/(label+'.log')).open('ab',buffering=0)as f:subprocess.run(['make','out/host/linux-x86/lib64/libart.so','-j3'],cwd=art,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=1200)
 target=out/(label+'-libart.so');shutil.copyfile(art/'out/host/linux-x86/lib64/libart.so',target);subprocess.run(['objcopy','--strip-debug',str(target)],check=True);return target
def abi(p):
 d={}
 for line in subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True).splitlines():
  v=line.split()
  if len(v)>=8 and v[0].rstrip(':').isdigit()and v[7]:d[v[7]]=(v[3],v[4],v[5],v[6]=='UND')
 return d
try:
 for n,h in old['patches'].items():
  patch=repo/'native/compat/patches'/n;assert sha(patch)==h;subprocess.run(['patch','--batch','--forward','--no-backup-if-mismatch','--fuzz=0','-p1','-i',str(patch)],cwd=art,check=True,capture_output=True)
 for n,v in expected.items():assert sha(art/n)==v['patched'],n
 baseline=build('baseline');assert sha(baseline)==old['binary_sha256'],'Current ART must reproduce byte-identical before ownership fix';print('ART291_BASELINE=byte-identical',flush=True)
 subprocess.run(['patch','--batch','--forward','--no-backup-if-mismatch','--fuzz=0','-p1','-i',str(repo/meta['patch'])],cwd=art,check=True,capture_output=True);assert sha(art/'art/runtime/thread_linux.cc')==meta['source_sha256'];candidate=build('candidate');assert abi(candidate)==abi(baseline),'Imported/exported dynamic ABI changed';shutil.copyfile(candidate,out/'libart.so');(out/'libart.so').chmod(0o644)
 record.update(passed=True,binary_sha256=sha(out/'libart.so'),baseline_reproduced_byte_identical=True,dynamic_abi_unchanged=True,source_meta_sha256=sha(repo/'native/compat/art-host-signal-stack-ownership/sources.json'),source=meta,builder_sha256=sha(Path(__file__)),baseline_manifest_sha256=sha(cts/'art240-host-math-precision-v1-build.json'),all_prior_patches=old['patches'],seconds=time.monotonic()-started)
except BaseException as error:record.update(error=repr(error),traceback=traceback.format_exc());traceback.print_exc()
finally:
 for n,(data,s)in sources.items():(art/n).write_bytes(data);os.utime(art/n,ns=(s.st_atime_ns,s.st_mtime_ns));assert (art/n).read_bytes()==data
 for n,v in backups.items():p=art/n;shutil.copyfile(backup/n,p);p.chmod(v['mode']);os.utime(p,ns=(v['atime_ns'],v['mtime_ns']));assert sha(p)==v['sha256']
 for p in inter.rglob('*'):
  if p.is_file()and str(p.relative_to(art))not in backups:p.unlink()
 record['vm_original_sources_objects_restored']=True;(out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(b/'art-build.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
assert record['passed']
