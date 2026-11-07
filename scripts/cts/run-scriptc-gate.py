#!/usr/bin/env python3
"""One unmodified official ScriptC test as an explicit, separate diagnostic."""
from pathlib import Path
import argparse,json,re,subprocess,hashlib
from official_archive import Archive
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--release',required=True);p.add_argument('--stage-bundle');p.add_argument('--linker-debug',action='store_true');p.add_argument('--trace-files',action='store_true');p.add_argument('--native-stacks',action='store_true');p.add_argument('--native-crash',action='store_true');p.add_argument('--module',choices=['CtsRenderscriptTestCases','CtsRsCppTestCases'],default='CtsRenderscriptTestCases');selection=p.add_mutually_exclusive_group();selection.add_argument('--test');selection.add_argument('--classes',nargs='+');p.add_argument('--max-seconds',type=int,default=80);a=p.parse_args()
assert 30<=a.max_seconds<=300
assert re.fullmatch(r'r[0-9]+-native-candidate',a.release)
repo=Path(__file__).resolve().parents[2];base=a.evidence.resolve();tag=a.release.split('-')[0]
suffix=('-debug'if a.linker_debug else'')+('-trace'if a.trace_files else'')+('-stacks'if a.native_stacks else'')+('-cpp'if a.module=='CtsRsCppTestCases'else'')+('-crash'if a.native_crash else'')
if a.test:
 assert re.fullmatch(r'[A-Za-z0-9_.]+#[A-Za-z0-9_]+',a.test)
 suffix+='-'+hashlib.sha256(a.test.encode()).hexdigest()[:8]
if a.classes:
 assert all(re.fullmatch(r'android\.renderscript\.cts\.[A-Za-z0-9_]+',name)for name in a.classes)
 suffix+='-'+hashlib.sha256(','.join(a.classes).encode()).hexdigest()[:8]
out=base/'gates'/('scriptc-'+tag+suffix);assert not out.exists();out.mkdir(parents=True)
plan=json.loads((base/'modules'/a.module/'inputs/plan.json').read_text())
test=','.join(a.classes)if a.classes else a.test or'android.renderscript.cts.AllocationCopy2DRangeTest#testAllocationCopy2DRange'
plan.update(label='cts'+tag[1:]+'-scriptc-allocation'+suffix,root='/home/art/releases/api29-'+a.release,timeout=a.max_seconds,arguments=dict(timeout_msec='15000',**{'class':test}))
plan['capture_process_maps']=True
if a.linker_debug:plan.update(linker_verbose=True,capture_rs_cache=True)
if a.trace_files:plan.update(trace_rs_files=True,capture_rs_cache=True)
if a.native_stacks:plan['capture_rs_native_stacks']=True
if a.native_crash:plan.update(capture_native_failure=True,capture_rs_cache=True)
archive=Archive(base/'official-index.json')
for item in plan['apks']:
 metadata=archive.extract('android-cts/testcases/'+item['file'],out/item['file']);assert metadata['sha256']==item['sha256']
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(out/'scope.json').write_text(json.dumps(dict(scope='Explicitly selected official tests, not complete CTS module acceptance',test=test,runtime=a.release,original_apks=plan['apks']),indent=2)+'\n')
vm=Path('/media/psf/Home/WorkSpace/saidroid-next');command=['prlctl','exec','MeeGo Build','/usr/bin/python3',str(vm/'scripts/cts/run-instrument-vm.py'),str(vm/(out/'plan.json').relative_to(repo))]
if a.stage_bundle:command+=['--stage-bundle',a.stage_bundle]
try:subprocess.run(command,check=True,timeout=400)
finally:
 for file in out.rglob('*.apk'):file.unlink()
result=json.loads((out/plan['label']/'run-result.json').read_text());counts={}
for line in(out/plan['label']/'instrumentation-events.jsonl').read_text().splitlines():
 e=json.loads(line)
 if e.get('event')=='status'and e.get('bundle',{}).get('test'):
  key={1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'}.get(e['code'],'other');counts[key]=counts.get(key,0)+1
summary=dict(status=result['status'],test=test,test_events=counts,scope='Selected unmodified official ScriptC tests',compositor_before=result.get('compositor_before'),compositor_after=result.get('compositor_after'),boot=result['boot'],lipstick=result['lipstick'],brightness=result['brightness'],cleanup_safe=not any(result.get(k)for k in['cleanup_error','cleanup_timeout','cleanup_process_alive'])and result['boot_unchanged']and result['lipstick_unchanged']and result['daily_root_unchanged'])
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
