#!/usr/bin/env python3
"""Targeted diagnostic repeat of three real View animation timeouts.

Keeps the complete-cohort result unchanged. Runs only after the serial batch.
Original APK, candidate, and assertions are unchanged; runner selection is an
explicit diagnostic override and cannot be presented as a full module pass.
"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess
from official_archive import Archive

p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--run',action='store_true');p.add_argument('--release',default='r130-native-candidate');p.add_argument('--bounded-visible',action='store_true');a=p.parse_args()
assert re.fullmatch(r'r[0-9]+-native-candidate',a.release)
repo=Path(__file__).resolve().parents[2];base=a.evidence.resolve()
tag=a.release.split('-')[0]
suffix=('-visible'if a.bounded_visible else'')
out=base/'gates'/(('view-timing-repeat'if tag=='r130'else'view-timing-repeat-'+tag)+suffix);out.mkdir(parents=True,exist_ok=True)
plan=json.loads((base/'modules/CtsViewTestCases/inputs/plan.json').read_text())
tests=[
 'android.view.animation.cts.AnimationSetTest#testGetTransformation',
 'android.view.animation.cts.AccelerateDecelerateInterpolatorTest#testAccelerateDecelerateInterpolator',
 'android.view.animation.cts.AccelerateInterpolatorTest#testAccelerateInterpolator',
]
plan.update(label='cts'+tag[1:]+'-view-timing-repeat'+suffix,root='/home/art/releases/api29-'+a.release,timeout=100,arguments=dict(timeout_msec='15000',**{'class':','.join(tests)}))
if a.bounded_visible:plan['visible_seconds']=45
apk=out/'CtsViewTestCases.apk'
archive=Archive(base/'official-index.json')
meta=archive.extract('android-cts/testcases/CtsViewTestCases.apk',apk)
assert meta['sha256']==plan['apks'][0]['sha256']
(out/'input-metadata.json').write_text(json.dumps(dict(scope='Three-test diagnostic repeat, not complete CTS module',tests=tests,input=meta,candidate=plan['root'],selection_override=True,bounded_visible_seconds=45 if a.bounded_visible else 0),indent=2)+'\n')
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
if a.run:
 vm=Path('/media/psf/Home/WorkSpace/saidroid-next')
 try:
  subprocess.run(['prlctl','exec','MeeGo Build','/usr/bin/python3',str(vm/'scripts/cts/run-instrument-vm.py'),str(vm/(out/'plan.json').relative_to(repo))],check=True,timeout=300)
 finally:
  # Retain one original input identity, no duplicated APK after the transaction.
  for file in out.rglob('*.apk'):file.unlink()
 result=json.loads((out/plan['label']/'run-result.json').read_text())
 counts={1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'};events={}
 for line in (out/plan['label']/'instrumentation-events.jsonl').read_text().splitlines():
  e=json.loads(line)
  if e.get('event')=='status'and e.get('bundle',{}).get('test'):
   key=counts.get(e['code'],'other');events[key]=events.get(key,0)+1
 summary=dict(scope='Explicit three-test diagnostic repeat; full-cohort failures retained',status=result['status'],test_events=events,tests=tests,boot=result['boot'],visible_diagnostic_seconds=result.get('visible_diagnostic_seconds',0),compositor_before=result.get('compositor_before'),compositor_after=result.get('compositor_after'),cleanup_safe=result.get('brightness')=='0'and result.get('boot_unchanged')and result.get('lipstick_unchanged')and result.get('daily_root_unchanged')and not any(result.get(k)for k in['cleanup_error','cleanup_timeout','cleanup_process_alive'])and all(result.get(k,{}).get('ready',True)for k in['compositor_before','compositor_after']))
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
else:print('DIAGNOSTIC_INPUT=prepared; no device operation')
