from pathlib import Path
import subprocess,json,time,hashlib
p=Path(__file__).parent;old=p/'full-boot-aot-v1';out=p/'full-boot-preloaded-v1';data=json.loads((old/'runtime-smoke-v3.json').read_text());build=json.loads((out/'result.json').read_text());assert build['passed']
for f in [out,out/'arm64',*(out/'arm64').iterdir()]:f.chmod(0o755 if f.is_dir()else 0o644)
cmd=[arg.replace(str(old/'arm64'),str(out/'arm64'))for arg in data['command']];start=time.monotonic()
with(out/'runtime-smoke-v1.log').open('xb')as log:q=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=90)
text=(out/'runtime-smoke-v1.log').read_text(errors='replace').replace('\0','');mapped=sorted(set(line.split()[-1]for line in text.splitlines()if line.startswith('MAP|')and'/'in line));images=[f for f in mapped if f.endswith('.art')];exec_oats=sorted(set(line.split()[-1]for line in text.splitlines()if line.startswith('MAP|')and' r-xp 'in line and line.endswith('.oat')))
passed=q.returncode==0 and 'FULL_BOOT_SMOKE=passed|'in text and images==data['images']and len(exec_oats)==15
result=dict(passed=passed,returncode=q.returncode,seconds=time.monotonic()-start,command=cmd,images=images,executable_oats=exec_oats,ordinary_uid=65534,hidden_api_denied_bits=3 if 'hidden_api_denied=3'in text else None,device_accessed=False,scope='Same exact ordinary ART smoke as K, changed only boot images from packaged preloaded list; not UI/CPU/PSS proof')
(out/'runtime-smoke-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in['command','images','executable_oats']},indent=2));assert passed
