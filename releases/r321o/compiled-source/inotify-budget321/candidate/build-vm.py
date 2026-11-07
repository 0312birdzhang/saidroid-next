from pathlib import Path
import hashlib,json,subprocess,platform,shutil
p=Path(__file__).resolve().parent;repo=Path('/media/psf/Home/WorkSpace/saidroid-next');assert platform.machine()=='aarch64'and str(p).startswith(str(repo))
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
recipe=p.parent/'inotify-budget-analysis-v1/local-native-overlay-v7/result.json';meta=json.loads(recipe.read_text());assert meta['candidate_sha256']=='226006ca8fe0d61e93210c5005da1b130f50a10046e3f2988067a3c0a1fcc65b'
source=p/'source';shutil.copytree(repo/'native/compat/inotify-budget',source,ignore=shutil.ignore_patterns('__pycache__'))
freeze=p/'baseline-source-freeze';freeze.mkdir();sources={}
for i,(name,digest)in enumerate(meta['input_sources'].items()):
 path=Path(name);assert sha(path)==digest;target=freeze/(str(i)+'-'+path.name);shutil.copyfile(path,target);sources[name]={'sha256':digest,'frozen':str(target)}
for name in ('syscall-aarch64.S',):assert sha(source/name)==sha(p.parent/'inotify-budget-analysis-v1/local-guard-source-v7'/name)
assembly=[s for s in meta['command']if s.endswith('.S')];assert len(assembly)==1
obj=p/'cc3Gq7RE.o';commands=[['gcc','-fPIC','-c',assembly[0],'-o',str(obj)]];subprocess.run(commands[0],check=True,timeout=20)
for label in ('baseline','candidate'):
 cmd=[str(obj)if s==assembly[0]else s for s in meta['command']];cmd[cmd.index('-o')+1]=str(p/(label+'.so'))
 if label=='candidate':
  indices=[i for i,x in enumerate(cmd)if x.endswith('/inotify-budget.c')];assert len(indices)==1;cmd[indices[0]]=str(source/'inotify-budget.c')
 commands.append(cmd)
 with(p/(label+'-build.log')).open('w')as out:subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=90)
 if label=='baseline':assert sha(p/'baseline.so')==meta['candidate_sha256']
def exports(path):return {tuple(s.split()[1:])for s in subprocess.check_output(['nm','-D','--defined-only',str(path)],text=True).splitlines()}
def needed(path):return [s for s in subprocess.check_output(['readelf','-d',str(path)],text=True).splitlines()if '(NEEDED)'in s]
assert exports(p/'baseline.so')==exports(p/'candidate.so');assert needed(p/'baseline.so')==needed(p/'candidate.so')
fixture_cmd=['gcc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-DSD_GUARD_FIXTURE','-o',str(p/'fixture.so'),str(source/'inotify-budget.c'),str(source/'syscall-aarch64.S'),'-pthread']
cancel_cmd=['gcc','-O2','-Wall','-Wextra','-Werror','-o',str(p/'cancel-fixture'),str(source/'cancel-fixture.c'),'-pthread','-ldl']
for label,cmd in [('fixture',fixture_cmd),('cancel',cancel_cmd)]:
 commands.append(cmd)
 with(p/(label+'-build.log')).open('w')as out:subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=30)
result={'passed':True,'baseline_byte_identical':True,'baseline_sha256':sha(p/'baseline.so'),'candidate_sha256':sha(p/'candidate.so'),'fixture_sha256':sha(p/'fixture.so'),'cancel_sha256':sha(p/'cancel-fixture'),'exports_unchanged':True,'dt_needed_unchanged':True,'only_changed_translation_unit':'inotify-budget.c','sources':sources,'candidate_sources':{f.name:sha(f)for f in source.iterdir()if f.is_file()},'commands':commands,'phone_accessed':False,'accepted_runtime_changed':False,'java_or_aot_inputs_changed':False}
(p/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ('commands','sources','candidate_sources')}),flush=True)
