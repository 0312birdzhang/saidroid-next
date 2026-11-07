#!/usr/bin/env python3
"""Summarize full attempt coverage separately from actual test completion."""
from pathlib import Path
import argparse,json,collections,xml.etree.ElementTree as ET
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);a=p.parse_args();base=a.evidence;plan=json.loads((base/'module-plan.json').read_text());states=collections.Counter();events=collections.Counter();runners=collections.Counter();versions=collections.Counter();native=collections.Counter();boots=collections.Counter();interruptions=[];rows=[]
for spec in plan['modules']:
 path=base/'modules'/spec['module']/'attempt.json'
 if not path.exists():rows.append(dict(module=spec['module'],status='NOT_ATTEMPTED'));continue
 value=json.loads(path.read_text());states[value['status']]+=1;versions[value['runtime']]+=1
 for r in value['runners']:
  runners[r['status']]+=1;events.update(r.get('test_events',{}))
  if r.get('boot'):boots[r['boot']]+=1
  if r['status']=='DEVICE_RESTART':interruptions.append(dict(module=value['module'],run=r.get('run'),boot=r.get('boot'),new_boot=r.get('new_boot'),reason=r.get('reason'),last_started_test=value.get('last_started_test'),evidence=value.get('interruption_evidence')))
 for source in (path.parent/'inputs').glob('native-result.json'):
  result=json.loads(source.read_text())
  if result.get('gtest_xml'):
   report=ET.fromstring(result['gtest_xml']);native['reports']+=1
   for key in ['tests','failures','disabled','errors']:native[key]+=int(report.get(key,'0'))
 rows.append(dict(module=value['module'],status=value['status'],runtime=value['runtime'],config_sha256=value['config_sha256'],formal_module_accepted=False,runners=[dict(type=r['type'],status=r['status'],reason=r.get('reason'),test_events=r.get('test_events',{}),run_outcome=r.get('run_outcome'),run=r.get('run'),boot=r.get('boot'),cleanup_safe=r.get('cleanup_safe'),native_runtime_scope=r.get('native_runtime_scope'))for r in value['runners']]))
summary=dict(abis_attempted=["arm64-v8a"],apk_install_modes_attempted=["full"],unimplemented_parameter_variants=["armeabi-v7a","instant_app","Android privileged/system preparation"],module_count=377,attempted=sum(states.values()),processed=sum(states.values())-states['RUNNING'],not_attempted=sum(r['status']=='NOT_ATTEMPTED'for r in rows),module_states=dict(states),runtime_distribution=dict(versions),runner_states=dict(runners),instrumentation_test_events=dict(events),native_host_gtest_xml=dict(native),native_scope='Original Android ELF under the phone system Android interpreter; not acceptance of the SailDroid glibc bridge.',formal_tradefed_runs=0,config_validation=({k:v for k,v in json.loads((base/'official-config-check.json').read_text()).items() if k!='modules'} if (base/'official-config-check.json').exists() else None),coverage_note='Module dispatch/preflight coverage is distinct from completed official CTS modules. A COMPLETED instrumentation runner may contain failed tests. Native XML totals include only preserved complete reports. Missing host/native/graphics contracts remain BLOCKED.',modules=rows)
summary['runner_boot_distribution']=dict(boots)
summary['device_interruptions']=interruptions
summary['boot_segments']=json.loads((base/'boot-segments.json').read_text())if(base/'boot-segments.json').exists()else None
summary['final_device_health']=json.loads((base/'final-health.json').read_text())if(base/'final-health.json').exists()else None
(base/'suite-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
# JUnit-format diagnostic report only; prominently labelled and never passed
# off as the Android CTS compatibility test_result.xml format.
root=ET.Element('testsuites',name='SailDroid official CTS attempt diagnostics (not Tradefed)',tests=str(len(rows)))
for row in rows:
 suite=ET.SubElement(root,'testsuite',name=row['module'],tests='1');case=ET.SubElement(suite,'testcase',name='official-module-dispatch',classname=row['module'])
 if row['status']in['BLOCKED','NOT_ATTEMPTED','NATIVE_HOST_EXECUTED','NO_TESTS']:
  ET.SubElement(case,'skipped',message=row['status']).text=json.dumps(row.get('runners',[]))
 elif row['status']!='EXECUTED':ET.SubElement(case,'failure',message=row['status']).text=json.dumps(row.get('runners',[]))
ET.indent(root);ET.ElementTree(root).write(base/'diagnostic-junit.xml',encoding='utf-8',xml_declaration=True)
print(json.dumps({k:v for k,v in summary.items()if k!='modules'},indent=2))
