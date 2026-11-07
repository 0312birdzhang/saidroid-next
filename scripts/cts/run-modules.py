#!/usr/bin/env python3
"""Dispatch every official configuration to its real compatible executor.
This is a SailDroid compatibility attempt ledger, not a Tradefed certificate.
Unimplemented host/native/preparer contracts remain explicit BLOCKED results.
"""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys,shutil,traceback,time,re,concurrent.futures,collections
from official_archive import Archive
from apk_manifest import parse
from instrumentation_outcome import inspect_finish,test_timeout_msec
from instrumentation_policy import hidden_api_checks
from runner_arguments import instrumentation_arguments
from temporary_directory_preparer import directory_spec
REPO=Path(__file__).resolve().parents[2];VMREPO=Path('/media/psf/Home/WorkSpace/saidroid-next')
def atomic(path,value):
 p=path.with_suffix('.pending');p.write_text(json.dumps(value,indent=2)+'\n');p.replace(path)
def option(spec,key,default=None):return next((x['value']for x in spec['options']if x.get('name')==key),default)
def main():
 p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--release',default='r116-native-candidate');p.add_argument('--modules',nargs='*');p.add_argument('--resume',action='store_true');p.add_argument('--max-seconds',type=int,default=240);p.add_argument('--stage-bundle');p.add_argument('--expected-boot');p.add_argument('--cross-package',action='store_true');p.add_argument('--module-timeouts',type=Path);p.add_argument('--capture-process-maps',action='store_true');p.add_argument('--vm-network-relay',action='store_true',help='Temporary process-only SOCKS over the existing SSH link; original endpoints and TLS remain unchanged');a=p.parse_args();ev=a.evidence.resolve();ev.mkdir(exist_ok=True,parents=True)
 plan=json.loads((ev/'module-plan.json').read_text());archive=Archive(ev/'official-index.json');bybase=collections.defaultdict(list)
 for name in archive.entries:bybase[Path(name).name].append(name)
 modules=plan['modules'];selected=set(a.modules)if a.modules else None
 network_proxy=dict(type='socks5',host='127.0.0.1',port=47151,transport='ssh-vm-loopback')if a.vm_network_relay else None
 known={m['module']for m in modules}
 unknown=selected-known if selected else set()
 if unknown:p.error('Unknown official module selection: '+', '.join(sorted(unknown)))
 # Run core framework contracts first, then all remaining official configs.
 priority={'CtsUtilTestCases':0,'CtsOsTestCases':1,'CtsPermissionTestCases':2,'CtsContentTestCases':3,'CtsAppTestCases':4}
 modules.sort(key=lambda m:(priority.get(m['module'],10),m['module']))
 def find(name):
  paths=bybase.get(name,[])
  preferred=[x for x in paths if x.startswith('android-cts/testcases/')]
  if len(preferred)==1:return preferred[0]
  if len(paths)==1:return paths[0]
  raise RuntimeError('Missing/ambiguous official input '+name)
 limits=json.loads(a.module_timeouts.read_text())if a.module_timeouts else {}
 unknown_limits=set(limits)-known
 if unknown_limits:p.error('Unknown official module timeout: '+', '.join(sorted(unknown_limits)))
 for name,limit in limits.items():assert isinstance(limit,int)and 30<=limit<=1800,(name,limit)
 ledger={};stage=a.stage_bundle
 for i,module in enumerate(modules):
  name=module['module']
  if selected and name not in selected:continue
  if (ev/'STOP_AFTER_MODULE').exists():
   print('SUITE_CONTROL=stopped-at-module-boundary',flush=True);break
  maximum=limits.get(name,a.max_seconds)
  out=ev/'modules'/name;out.mkdir(parents=True,exist_ok=True);recordpath=out/'attempt.json'
  if a.resume and recordpath.exists():
   prior=json.loads(recordpath.read_text())
   if prior['status']!='RUNNING':ledger[name]=prior;continue
   raise RuntimeError('Unfinished module requires evidence reconciliation before resume: '+name)
  label=('cts'+a.release.split('-')[0].removeprefix('r')+'-'+str(i).zfill(3)+'-'+str(time.time_ns())[-7:]);work=out/'inputs';work.mkdir(exist_ok=True)
  result=dict(module=name,status='RUNNING',cts='10_r16-arm',runtime=a.release,config_sha256=module['config_sha256'],formal_tradefed=False,attempt_limits=dict(module_timeout_seconds=maximum,runner_test_timeout_msec=None,runner_test_timeouts_msec={},runner_timeout_policy='original-config-or-Tradefed-default',standard_android_preparers_fully_satisfied=False,formal_module_acceptance=False,network_proxy=network_proxy),started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),runners=[],inputs=[],preparers=module['preparers'])
  atomic(recordpath,result);print('MODULE_START='+name,flush=True)
  try:
   apk_names=sorted({o['value']for prep in module['preparers']for o in prep['options']if o.get('name')=='test-file-name'and o['value'].endswith('.apk')})
   java_runners=[r for r in module['runners']if r.get('class','').endswith(('AndroidJUnitTest','LibcoreTest'))]
   if java_runners:
    def fetch(apk):
     path=work/apk;metadata=archive.extract(find(apk),path);manifest=parse(path);return dict(metadata,package=manifest['package'],file=apk,manifest=manifest)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:apks=list(pool.map(fetch,apk_names))
    result['inputs']=[{k:v for k,v in item.items()if k!='manifest'}for item in apks]
    configs=[];pushed=[]
    for prep in module['preparers']:
     if not prep.get('class','').endswith('DynamicConfigPusher')or option(prep,'target')!='device':continue
     filename=option(prep,'config-filename');assert filename and re.fullmatch(r'[A-Za-z0-9_.-]+',filename)
     source=option(prep,'dynamic-config-name',filename)+'.dynamic';path=work/source;metadata=archive.extract(find(source),path)
     prepared=work/(filename+'.prepared.dynamic');command=['prlctl','exec','MeeGo Build','/usr/bin/python3',str(VMREPO/'scripts/cts/prepare-dynamic-vm.py'),str(VMREPO/path.relative_to(REPO)),filename,option(prep,'version','10_r16'),str(VMREPO/prepared.relative_to(REPO))]
     with(out/('prepare-'+filename+'.log')).open('w')as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=50)
     preparation=json.loads(Path(str(prepared)+'.metadata.json').read_text());sha=hashlib.sha256(prepared.read_bytes()).hexdigest()
     configs.append(dict(name=filename+'.dynamic',file=prepared.name,sha256=sha));result['inputs'].append(dict(metadata,prepared_sha256=sha,preparation=preparation))
    for prep in module['preparers']:
     if not prep.get('class','').endswith('FilePusher'):continue
     for entry in prep['options']:
      value=entry.get('value','')
      if entry.get('name')not in['push-file','push']or '->'not in value:continue
      source,destination=value.split('->',1)
      if not destination.startswith('/data/local/tmp/signature-test/'):continue
      assert re.fullmatch(r'[A-Za-z0-9_.-]+',source)and Path(destination).name==destination.removeprefix('/data/local/tmp/signature-test/')
      metadata=archive.extract(find(source),work/source);pushed.append(dict(file=source,destination=destination,sha256=metadata['sha256']));result['inputs'].append(dict(metadata,destination=destination))
    for n,runner in enumerate(java_runners):
     runner_result=dict(type=runner['class'],status='BLOCKED');package=option(runner,'package');runner_result['package']=package
     main=next((x for x in apks if x['package']==package),None)
     if main is None:runner_result['reason']='Declared test package is absent from the official APK preparation set';result['runners'].append(runner_result);continue
     instrumentations=main['manifest']['instrumentation'];wanted=option(runner,'runner')
     selected_instrument=next((x for x in instrumentations if not wanted or x['name']==wanted),None)
     if selected_instrument is None:runner_result['reason']='No matching declared Instrumentation';result['runners'].append(runner_result);continue
     target=selected_instrument['targetPackage'];runner_result['target']=target
     if target!=package and not a.cross_package:runner_result['reason']='Cross-package Instrumentation target binding is not enabled in this pinned runtime';result['runners'].append(runner_result);continue
     if target!=package and not any(x['package']==target for x in apks):runner_result['reason']='Official Instrumentation target APK is missing from module preparation';result['runners'].append(runner_result);continue
     args=instrumentation_arguments(runner)
     # Honor the original host runner timeout, rather than introducing a
     # shorter interrupt into an otherwise successful long native test.
     args.setdefault('timeout_msec',str(test_timeout_msec(runner)))
     runner_result['test_timeout_msec']=int(args['timeout_msec'])
     result['attempt_limits']['runner_test_timeouts_msec'][str(n)]=int(args['timeout_msec'])
     values=set(result['attempt_limits']['runner_test_timeouts_msec'].values())
     result['attempt_limits']['runner_test_timeout_msec']=next(iter(values))if len(values)==1 else None
     runlabel=label+'-'+str(n);spec=dict(label=runlabel,module=name,root='/home/art/releases/api29-'+a.release,package=target,test_package=package,component=package+'/'+selected_instrument['name'],arguments=args,timeout=maximum,expected_boot=a.expected_boot,apks=[dict(**{k:x[k]for k in ['package','file','sha256']},debuggable=x['manifest']['application'].get('debuggable',False))for x in apks],dynamic_configs=configs,pushed_files=pushed)
     directories=directory_spec(module['preparers'])
     if directories:spec['directory_preparation']=directories
     spec['hidden_api_checks']=hidden_api_checks(runner)
     spec['official_config_sha256']=module['config_sha256']
     runner_result['hidden_api_checks']=spec['hidden_api_checks']
     if a.capture_process_maps:spec['capture_process_maps']=True
     if network_proxy:spec['network_proxy']=network_proxy
     runplan=work/'plan.json';atomic(runplan,spec)
     command=['prlctl','exec','MeeGo Build','/usr/bin/python3',str(VMREPO/'scripts/cts/run-instrument-vm.py'),str(VMREPO/runplan.relative_to(REPO))]
     if stage:command+=['--stage-bundle',stage];stage=None
     with(out/('runner-'+str(n)+'.log')).open('w')as log:
      try:run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=maximum+300)
      except subprocess.TimeoutExpired as error:raise RuntimeError('Device cleanup/identity evidence missing after orchestration deadline; abort serial suite')from error
     runout=work/runlabel
     if runout.exists():
      destination=out/runlabel;runout.rename(destination);runresult=destination/'run-result.json'
      for duplicate in destination.glob('*.apk'):duplicate.unlink()
      if runresult.exists():
       data=json.loads(runresult.read_text());runner_result.update(status=data['status'],run=runlabel,pid=data.get('pid'),cleanup_safe=data.get('brightness')=='0'and data.get('boot_unchanged')and data.get('lipstick_unchanged')and data.get('daily_root_unchanged')and not any(data.get(k)for k in ['cleanup_error','cleanup_timeout','cleanup_process_alive'])and all(data.get(k,{}).get('ready',True)for k in ['compositor_before','compositor_after']))
       if spec.get('directory_preparation'):
        runner_result['directory_preparation']=data.get('directory_preparation')
        runner_result['cleanup_safe']=runner_result['cleanup_safe']and data.get('directory_preparation',{}).get('cleaned')is True
       for key in ['compositor_before','compositor_after']:
        if key in data:runner_result[key]=data[key]
       events=destination/'instrumentation-events.jsonl';counts=collections.Counter()
       if events.exists():
        for line in events.read_text().splitlines():
         event=json.loads(line)
         if event['event']=='status'and 'test'in event['bundle']:
          code=event['code'];counts[{1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'}.get(code,'other')]+=1
       runner_result['test_events']=dict(counts)
       if runner_result['status']=='COMPLETED'and not counts:runner_result.update(status='NO_TESTS',reason='Runner finished without any individual test status; no test execution is claimed')
       if data.get('instrumentation'):runner_result['finish']=data['instrumentation']
       runner_result['run_outcome']=inspect_finish(data.get('instrumentation'),counts)
       if run.returncode or not runner_result['cleanup_safe']:
        runner_result['status']='BLOCKED_CLEANUP'
        runner_result['reason']='Device cleanup/identity contract failed; serial suite must stop'
        result['runners'].append(runner_result)
        raise RuntimeError('Device cleanup/identity contract failed; abort serial suite')
      else:
       runner_result.update(status='ERROR',reason='No result after VM/device attempt',exit=run.returncode)
     else:runner_result.update(status='ERROR',reason='No device evidence directory',exit=run.returncode)
     if runner_result['status']=='ERROR':
      runner_result.update(status='BLOCKED_CLEANUP',reason='No authoritative device result/cleanup proof; serial suite must stop')
      result['runners'].append(runner_result)
      raise RuntimeError('Device cleanup/identity evidence missing; abort serial suite')
     result['runners'].append(runner_result)
   for runner in module['runners']:
    kind=runner.get('class','')
    if runner in java_runners:continue
    if kind.endswith('GTest'):
     binary=option(runner,'module-name',name)+'64'
     path=work/binary;metadata=archive.extract(find(binary),path);result['inputs'].append(metadata)
     # Native executable handoff uses the real phone ELF interpreter check;
     # it never substitutes a glibc-compiled test for the Android binary.
     nativeplan=work/'native-plan.json';atomic(nativeplan,dict(module=name,label=label+'-native',binary=binary,sha256=metadata['sha256'],runtime=a.release,expected_boot=a.expected_boot))
     cmd=['prlctl','exec','MeeGo Build','/usr/bin/python3',str(VMREPO/'scripts/cts/run-native-vm.py'),str(VMREPO/nativeplan.relative_to(REPO))]
     with(out/'native-run.log').open('w')as log:
      try:native_process=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=210)
      except subprocess.TimeoutExpired as error:raise RuntimeError('Device cleanup/identity evidence missing after native deadline; abort serial suite')from error
     if native_process.returncode:raise RuntimeError('Device cleanup/identity evidence missing after native transaction; abort serial suite')
     nr=json.loads((work/'native-result.json').read_text());result['runners'].append(dict(type=kind,**nr))
    else:
     # Dispatch the actual executor preflight for host/GL/Dalvik families.
     # Missing Android transport/HAL is a blocker, never a synthetic pass.
     result['runners'].append(dict(type=kind,status='BLOCKED',reason='Official '+kind.rsplit('.',1)[-1]+' requires a Tradefed Android target/ADB and system preparation; live target preflight has no adbd/am/pm/system_server',preflight='target-preflight.json',options=runner['options']))
   statuses={r['status']for r in result['runners']}
   if not statuses:result.update(status='BLOCKED',reason='Official configuration has no executable test runner (support/data configuration)')
   elif statuses=={'COMPLETED'}:result['status']='EXECUTED'
   elif statuses=={'EXECUTED'}:result['status']='NATIVE_HOST_EXECUTED'
   elif statuses=={'NO_TESTS'}:result['status']='NO_TESTS'
   elif statuses=={'BLOCKED'}:result['status']='BLOCKED'
   else:result['status']='ATTEMPTED_WITH_FAILURES'
   if any(r.get('test_events',{}).get('failed',0)or r.get('test_events',{}).get('error',0)or r.get('run_outcome',{}).get('has_failures')for r in result['runners']):result['status']='FAILED'
  except Exception as error:
   result.update(status='ERROR',reason=str(error),traceback=traceback.format_exc());print('MODULE_ERROR='+name+'|'+str(error),flush=True)
   if 'cleanup/identity'in str(error):atomic(recordpath,result);raise
  finally:
   # Keep metadata, event streams and logs; remove APK/ELF input copies after
   # the verified device transaction. The official range source is reproducible.
   if work.exists():
    for file in work.rglob('*'):
     if file.is_file()and(file.suffix=='.apk'or file.name.endswith('64')or file.suffix=='.partial'):file.unlink()
  result['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());atomic(recordpath,result);ledger[name]=result
  allrows=[json.loads(f.read_text())for f in (ev/'modules').glob('*/attempt.json')];summary=dict(modules_total=377,processed=len([r for r in allrows if r['status']!='RUNNING']),states=dict(collections.Counter(r['status']for r in allrows)),formal_tradefed=False,runtime=a.release)
  atomic(ev/'suite-progress.json',summary);print('MODULE_END='+name+'|'+result['status']+'|'+str(summary['processed'])+'/377',flush=True)
if __name__=='__main__':main()
