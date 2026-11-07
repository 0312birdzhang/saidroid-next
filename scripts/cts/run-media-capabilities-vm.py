#!/usr/bin/env python3
"""Run a signed public API snapshot, separate from official CTS evidence."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--expected-boot',required=True);a=p.parse_args()
assert a.release in ['r172-native-candidate','r173-native-candidate']
repo=Path('/media/psf/Home/WorkSpace/saidroid-next');base=repo/'build/evidence/cts-frame-repair-20261031';built=Path('/var/tmp/saidroid-private-media-capabilities-20261031');manifest=json.loads((built/'manifest.json').read_text());apk=manifest['apks'][0];tag=a.release.split('-')[0];out=base/'gates'/('public-media-'+tag);out.mkdir()
assert not any(json.loads(f.read_text())['status']=='RUNNING'for f in(base/'modules').glob('*/attempt.json'))
label='cts'+tag[1:]+'-private-public-media-snapshot';plan=dict(label=label,module='PrivatePublicMediaSnapshot',root='/home/art/releases/api29-'+a.release,package=apk['package'],test_package=apk['package'],component=apk['package']+'/org.example.saildroid.mediacapabilities.MediaCapabilitiesInstrumentation',arguments={},timeout=90,expected_boot=a.expected_boot,apks=[apk],dynamic_configs=[],pushed_files=[],hidden_api_checks=True)
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');source=built/apk['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==apk['sha256'];shutil.copyfile(source,out/source.name)
try:subprocess.run(['python3',str(repo/'scripts/cts/run-instrument-vm.py'),str(out/'plan.json')],check=True)
finally:(out/source.name).unlink(missing_ok=True)
result=json.loads((out/label/'run-result.json').read_text());assert result['status']=='COMPLETED'and result['brightness']=='0'and all(result[k]for k in ['boot_unchanged','lipstick_unchanged','daily_root_unchanged'])
assert not any(result.get(k)for k in ['cleanup_error','cleanup_timeout','cleanup_process_alive'])and all(result[k]['ready']for k in ['compositor_before','compositor_after'])
events=[json.loads(l)for l in(out/label/'instrumentation-events.jsonl').read_text().splitlines()];assert sum(v.get('event')=='status'and v.get('code')==0 for v in events)==1 and not any(v.get('event')=='status'and v.get('code')in[-1,-2]for v in events)
finish=result['instrumentation'];assert finish['code']==-1;values=finish['results'];support=json.loads(values['support_snapshot']);sha=hashlib.sha256(json.dumps(support,sort_keys=True).encode()).hexdigest()
report=dict(scope='Internal ordinary signed public API snapshot; not CTS acceptance',runtime=a.release,support=support,support_sha256=sha,measured_320x180=values['measured_320x180'],apk_sha256=apk['sha256'],cleanup_safe=True)
if tag=='r173':
 before=json.loads((base/'public-media-r172.json').read_text());assert before['support']==support and before['apk_sha256']==apk['sha256'],'Native coding capabilities changed'
 assert before['measured_320x180']!=report['measured_320x180'],'Private measured metadata did not load'
 report['native_coding_capabilities_unchanged']=True
(base/('public-media-'+tag+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
