from pathlib import Path
import os,subprocess,json,hashlib,time,shutil,argparse
p=argparse.ArgumentParser();p.add_argument("--art-source",type=Path,required=True);p.add_argument("--baseline-art",type=Path,required=True);p.add_argument("--output",type=Path,required=True);args=p.parse_args();os.umask(0o022)
repo=Path(__file__).resolve().parents[2];base=repo/'build/evidence/cts-frame-repair-20261031';art=args.art_source;out=args.output;out.mkdir();os.environ['JAVA_HOME']='/tmp/jdkfull/jdk-21.0.13+9';os.environ['PATH']=os.environ['JAVA_HOME']+'/bin:'+os.environ['PATH'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();names=['art/runtime/ti/agent.cc','art/runtime/native/java_lang_VMClassLoader.cc','art/runtime/entrypoints/entrypoint_utils-inl.h','art/runtime/thread_linux.cc'];sources={n:((art/n).read_bytes(),(art/n).stat())for n in names};inter=art/'out/host/linux-x86/obj/SHARED_LIBRARIES/libart_intermediates';files=[p for p in inter.rglob('*')if p.is_file()]+[art/'out/host/linux-x86/lib64/libart.so',art/'out/host/linux-x86/obj/lib/libart.so'];backups={};start=time.monotonic()
for f in files:
 n=str(f.relative_to(art));target=out/'original'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);backups[n]=sha(f)
expected=json.loads((args.baseline_art/'manifest.json').read_text());assert expected['passed']and sha(args.baseline_art/'libart.so')==expected['binary_sha256']=='929cdae7a4ab8587c5b4c8cb5866f545cbffdbe185877918b3cb9326e26d8f37';meta=json.loads((repo/'native/compat/art-host-signal-stack/sources.json').read_text());assert sha(repo/meta['source'])==meta['source_sha256']and sha(repo/meta['patch'])==meta['patch_sha256']and sha(art/'art/runtime/thread_linux.cc')==meta['baseline_sha256'];assert all(sha(art/n)==v['restored_vm_source_sha256']for n,v in expected['source_manifest'].items())
patches=['art-agent-bionic-symbol.patch','art-boot-resource-path.patch','art-interface-object-dispatch.patch','art-host-signal-stack.patch'];patched={};record=dict(scope='Isolated ART Linux/glibc native guarded alternate signal stacks min256KiB with runtime minimum and matchingteardown. Retains actual agent/resource/interface194 patches. No managedheap/JIT/test/clock/timeout/phone change; all baseline VM source/object bytes restored.',passed=False)
try:
 for n in patches:subprocess.run(['patch','--batch','--forward','-p1','-i',str(repo/'native/compat/patches'/n)],cwd=art,check=True,capture_output=True)
 for n in names:
  patched[n]=sha(art/n);target=out/'patched'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(art/n,target)
 dry=subprocess.run(['make','-n','out/host/linux-x86/lib64/libart.so','-j3'],cwd=art,capture_output=True,text=True,check=True,timeout=45);(out/'dry-run.log').write_text(dry.stdout)
 with(out/'build.log').open('w')as log:subprocess.run(['make','out/host/linux-x86/lib64/libart.so','-j3'],cwd=art,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
 binary=out/'libart.so';shutil.copy2(art/'out/host/linux-x86/lib64/libart.so',binary)
 def abi(p):
  text=subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True);return sorted(' '.join(l.split()[3:])for l in text.splitlines()if l.strip()and l.strip()[0].isdigit())
 assert abi(binary)==abi(args.baseline_art/'libart.so'),'Public/imported ABI changed'
 subprocess.run(['objcopy','--strip-debug',str(binary)],check=True)
 record.update(passed=True,builder_sha256=sha(Path(__file__)),source_meta_sha256=sha(repo/'native/compat/art-host-signal-stack/sources.json'),baseline_binary_sha256=sha(args.baseline_art/'libart.so'),binary_sha256=sha(binary),sources={n:dict(base_sha256=hashlib.sha256(v[0]).hexdigest(),patched_sha256=patched[n])for n,v in sources.items()},patches={n:sha(repo/'native/compat/patches'/n)for n in patches},abi_unchanged=True,seconds=time.monotonic()-start)
except BaseException as e:record.update(error=repr(e),traceback=__import__('traceback').format_exc())
finally:
 for n,(data,stamp)in sources.items():(art/n).write_bytes(data);os.utime(art/n,ns=(stamp.st_atime_ns,stamp.st_mtime_ns));assert(art/n).read_bytes()==data
 for n,h in backups.items():shutil.copy2(out/'original'/n,art/n);assert sha(art/n)==h
 old=set(backups)
 for p in inter.rglob('*'):
  if p.is_file()and str(p.relative_to(art))not in old:p.unlink()
 record['vm_baseline_sources_and_objects_restored']=True;(out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(base/'art220-host-signal-stack-v1-build.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
assert record['passed']
