#!/usr/bin/env python3
"""Run an explicit original-test selection, separate from complete module results."""
from pathlib import Path
import argparse,collections,hashlib,json,re,subprocess
from official_archive import Archive
from apk_manifest import parse
from instrumentation_outcome import inspect_finish,test_timeout_msec
from instrumentation_policy import hidden_api_checks

def main():
 p=argparse.ArgumentParser()
 p.add_argument('evidence',type=Path);p.add_argument('--source-plan',type=Path,required=True)
 p.add_argument('--release',required=True);p.add_argument('--expected-boot',required=True)
 p.add_argument('--test',required=True);p.add_argument('--stage-bundle');p.add_argument('--native-crash',action='store_true');p.add_argument('--capture-rs-cache',action='store_true')
 p.add_argument('--max-seconds',type=int,default=90)
 p.add_argument('--attempt',type=int,help='Independent repetition ID; each attempt retains its own immutable evidence')
 a=p.parse_args();repo=Path(__file__).resolve().parents[2];base=a.evidence.resolve();base.relative_to(repo)
 assert re.fullmatch(r'r[0-9]+-native-candidate',a.release)
 assert re.fullmatch(r'[A-Za-z0-9_.]+(?:#[A-Za-z0-9_]+)?',a.test)
 assert re.fullmatch(r'[a-f0-9-]{36}',a.expected_boot)and 30<=a.max_seconds<=900
 assert a.attempt is None or 1<=a.attempt<=10000
 raw=a.source_plan.read_bytes();plan=json.loads(raw);name=plan['module']
 official=json.loads((base/'module-plan.json').read_text())
 module=next(m for m in official['modules']if m['module']==name)
 assert any(r.get('class','').endswith('AndroidJUnitTest')for r in module['runners'])
 tag=a.release.split('-')[0];selection=hashlib.sha256(a.test.encode()).hexdigest()[:8]
 suffix=('-crash'if a.native_crash else'')+('-cache'if a.capture_rs_cache else'')
 if a.attempt is not None:suffix+='-attempt'+str(a.attempt).zfill(4)
 out=base/'gates'/('selected-'+tag+'-'+name+'-'+selection+suffix);assert not out.exists();out.mkdir(parents=True)
 label='cts'+tag[1:]+'-selected-'+hashlib.sha256(name.encode()).hexdigest()[:8]+'-'+selection+suffix
 runner=next(r for r in module['runners']if r.get('class','').endswith('AndroidJUnitTest')and any(o.get('name')=='package'and o.get('value')==plan['test_package']for o in r['options']))
 plan.update(label=label,root='/home/art/releases/api29-'+a.release,expected_boot=a.expected_boot,timeout=a.max_seconds,arguments=dict(timeout_msec=str(test_timeout_msec(runner)),**{'class':a.test}))
 plan['hidden_api_checks']=hidden_api_checks(runner)
 plan['official_config_sha256']=module['config_sha256']
 # Diagnostics do not leak from an archived source plan into ordinary checks.
 for key in ['capture_native_failure','capture_rs_cache','capture_rs_native_stacks','capture_cfi_timing','linker_verbose','trace_rs_files','visible_seconds']:plan.pop(key,None)
 if a.native_crash:plan.update(capture_native_failure=True,capture_process_maps=True)
 if a.capture_rs_cache:
  assert name in['CtsRenderscriptTestCases','CtsRenderscriptLegacyTestCases','CtsRsCppTestCases']
  plan['capture_rs_cache']=True
 assert not plan.get('pushed_files')and not plan.get('dynamic_configs'),'Selected helper needs explicit preparer support for this source'
 archive=Archive(base/'official-index.json')
 try:
  for item in plan['apks']:
   file=out/item['file'];metadata=archive.extract('android-cts/testcases/'+item['file'],file)
   assert metadata['sha256']==item['sha256']and parse(file)['package']==item['package']
  (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
  (out/'scope.json').write_text(json.dumps(dict(scope='Explicit selection from unmodified official APKs; not a complete module or Tradefed acceptance',source_plan=str(a.source_plan),source_plan_sha256=hashlib.sha256(raw).hexdigest(),module=name,original_config_sha256=module['config_sha256'],selection=a.test,runtime=a.release,attempt=a.attempt,diagnostic=a.native_crash or a.capture_rs_cache),indent=2)+'\n')
  vm=Path('/media/psf/Home/WorkSpace/saidroid-next');command=['prlctl','exec','MeeGo Build','/usr/bin/python3',str(vm/'scripts/cts/run-instrument-vm.py'),str(vm/(out/'plan.json').relative_to(repo))]
  if a.stage_bundle:command+=['--stage-bundle',a.stage_bundle]
  subprocess.run(command,check=True,timeout=a.max_seconds+300)
 finally:
  for file in out.glob('*.apk'):file.unlink()
 directory=out/label;result=json.loads((directory/'run-result.json').read_text());counts=collections.Counter()
 for line in(directory/'instrumentation-events.jsonl').read_text().splitlines():
  event=json.loads(line)
  if event.get('event')=='status'and event.get('bundle',{}).get('test'):counts[{1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'}.get(event['code'],'other')]+=1
 safe=result['brightness']=='0'and all(result[k]for k in ['boot_unchanged','lipstick_unchanged','daily_root_unchanged'])and not any(result.get(k)for k in ['cleanup_error','cleanup_timeout','cleanup_process_alive'])and all(result[k]['ready']for k in ['compositor_before','compositor_after'])
 outcome=inspect_finish(result.get('instrumentation'),counts)
 summary=dict(status=result['status'],module=name,selection=a.test,runtime=a.release,test_events=dict(counts),run_outcome=outcome,scope='Explicit diagnostic selection, not complete module acceptance',boot=result['boot'],lipstick=result['lipstick'],brightness=result['brightness'],cleanup_safe=safe,compositor_before=result['compositor_before'],compositor_after=result['compositor_after'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));assert safe
if __name__=='__main__':main()
