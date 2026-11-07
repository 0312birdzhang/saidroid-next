#!/usr/bin/env python3
"""Derive private device performance metadata from original CTS log measurements.

This does not change a runtime or a test result. At least 20 independently
recorded rounds are required for every published codec/size, as in AOSP.
An independent original-APK holdout must validate any subsequently installed XML.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math,re,types

SOURCE_SHA='1f879f25ba92862ec766debbf128bc9ca3a8aa6934026a3d0a662a7ab0a7b2b1'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def original_generator(source):
 assert digest(source)==SOURCE_SHA,'Expected unmodified Android 10 r16 measurement tool'
 text=source.read_text()
 # Load only the original pure percentile/XML functions. The Python-2 CLI
 # expects a Tradefed ZIP; no fabricated ZIP/device-info input is constructed.
 code=text[text.index('def perc('):text.index('\n\nclass Data:')]
 assert code.count('N / 2')==3
 code=code.replace('N / 2','N // 2')
 # Python 2 rounds positive ties away from zero. Rates and percentile indices
 # are non-negative; retain that rule instead of Python 3's ties-to-even.
 def py2round(value,places=0):
  factor=10.**places
  return math.copysign(math.floor(abs(value)*factor+0.5)/factor,value)
 namespace=dict(math=math,round=py2round)
 exec(compile(code,str(source)+'[pure-functions-python3]', 'exec'),namespace)
 return namespace['genXml'],code

def collect(directory,codec,width,height,expected_root):
 plan_path=directory.parent/'plan.json'
 if not plan_path.is_file():plan_path=directory.parent/'inputs/plan.json'
 plan=json.loads(plan_path.read_text())
 # Complete module runs keep the plan in inputs/, selected runs beside result.
 assert plan['root']==expected_root and plan['module']=='CtsVideoTestCases'
 assert len(plan['apks'])==1 and plan['apks'][0]['sha256']=='ca098877e5e1ad99ffca5a22af4526478efcc644166676923655c4ae2f68c1e9'
 result=json.loads((directory/'run-result.json').read_text())
 assert result['brightness']=='0' and all(result[k] for k in ['boot_unchanged','lipstick_unchanged','daily_root_unchanged'])
 assert not any(result.get(k) for k in ['cleanup_error','cleanup_timeout','cleanup_process_alive'])
 assert all(result[k]['ready'] for k in ['compositor_before','compositor_after'])
 log=directory/'android.video.cts.log';points=[];seen=set()
 pattern=re.compile(r'(\w+)=(\{[^}]*\}|[^ ,{}]+)')
 for number,line in enumerate(log.read_text(errors='replace').splitlines(),1):
  if '|tag=MediaPerfUtils|encoder stats:' not in line or 'windowMs=1000 ' not in line:continue
  fields=dict(pattern.findall(line))
  if fields.get('codec')!=codec:continue
  fmt=dict(re.findall(r'(\w[\w-]*)=([^, }]+)',fields['configFormat']))
  if (int(fmt['width']),int(fmt['height']))!=(width,height):continue
  round_number=int(fields['round']);assert round_number not in seen,'Duplicate round in one selected attempt'
  seen.add(round_number);p95=int(fields['p95']);assert p95>0 and int(fields['num'])>0
  points.append(dict(round=round_number,codec=codec,mime=fmt['mime'],width=width,height=height,
   p95_us=p95,fps=1e6/p95,source_line=number,source_log=str(log),source_log_sha256=digest(log),
   request_sha256=digest(plan_path),result_sha256=digest(directory/'run-result.json'),
   runtime=plan['root'],run_id=plan['label'],original_apk_sha256=plan['apks'][0]['sha256'],
   original_test_outcome=result['status']))
 return points

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--runtime-root',required=True);p.add_argument('--codec',required=True)
 p.add_argument('--codec-identity',type=Path);p.add_argument('--codec-identity-after',type=Path)
 p.add_argument('--width',type=int,required=True);p.add_argument('--height',type=int,required=True)
 p.add_argument('runs',nargs='+',type=Path);a=p.parse_args()
 assert not a.out.exists(),'Evidence output is immutable; choose a new directory'
 generate,ported=original_generator(a.source);a.out.mkdir(parents=True)
 points=[];seen=set()
 for run in a.runs:
  for point in collect(run,a.codec,a.width,a.height,a.runtime_root):
   identity=(point['run_id'],point['round']);assert identity not in seen,'Repeated evidence is not an independent sample'
   seen.add(identity);points.append(point)
 (a.out/'samples.json').write_text(json.dumps(points,indent=2)+'\n')
 (a.out/'aosp-pure-functions-python3.py').write_text(ported)
 report=dict(scope='Measured metadata generation only; no runtime installation or CTS acceptance',
  source_sha256=SOURCE_SHA,python3_changes=['N / 2 to N // 2 at three original integer operations','preserve Python 2 positive tie rounding'],
  sampling='Original MediaPerfUtils windowMs=1000 p95 logged in rounded microseconds; no fabricated reportlog/device-info',
  required_rounds=20,actual_rounds=len(points),runtime=a.runtime_root,independent_holdout_required=True)
 if a.codec_identity or a.codec_identity_after:
  assert a.codec_identity and a.codec_identity_after
  during=json.loads(a.codec_identity.read_text());after=json.loads(a.codec_identity_after.read_text())
  assert during['host_codec_processes'] and during['private_root']==a.runtime_root
  for key in ['boot','private_root','private','host_encoder','host_performance_xml']:
   assert during[key]==after[key],'Actual media implementation changed during measurements: '+key
  report['implementation_identity']=during
  report['implementation_identity_evidence']={str(p):digest(p)for p in [a.codec_identity,a.codec_identity_after]}
 if len(points)<20:
  report.update(status='BLOCKED_INSUFFICIENT_SAMPLES')
 else:
  Size=collections.namedtuple('Size','width height');Size.__str__=lambda self:'%dx%d'%self
  mime={v['mime']for v in points};assert len(mime)==1
  data={(False,a.codec.lower().startswith('omx.google.'),next(iter(mime)),a.codec):{Size(a.width,a.height):[v['fps']for v in points]}}
  xml='\n'.join(generate(data,types.SimpleNamespace(ignore=False,dbg=False)))+'\n'
  (a.out/'media_codecs_performance.xml').write_text(xml)
  report.update(status='GENERATED_NOT_INSTALLED',xml_sha256=digest(a.out/'media_codecs_performance.xml'))
 (a.out/'provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
