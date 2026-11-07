from pathlib import Path
import json,subprocess,time
p=Path(__file__).parent/'full-boot-aot-v1';old=json.loads((p/'runtime-smoke-v2.json').read_text());work=Path('/var/tmp/saidroid-fullboot-smoke-v1')
for f in [work,*work.rglob('*'),p/'arm64',*(p/'arm64').iterdir()]:
 if f.is_dir():f.chmod(0o777 if f==work/'data'else 0o755)
 elif f.is_file():f.chmod(0o644)
start=time.monotonic();cmd=old['command'];root=Path('/opt/saildroid/releases/api29-r321j-dev-20261105');bootstrap=str(root/'lib/java-cli-bootstrap.jar')
cmd=[arg+':'+bootstrap if arg.startswith(('-Xbootclasspath:','-Xbootclasspath-locations:')) else arg for arg in cmd]
cmd[-1:]=['SdJavaCommand','FullBootSmoke']
pos=cmd.index('-cp');cmd[pos:pos]=['-Dsaidroid.bridge.library='+str(root/'lib/libsdbridge.so'),'-Dsaidroid.native.runtime='+str(root/'android-libs')]
with(p/'runtime-smoke-v3.log').open('xb')as log:q=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=90)
text=(p/'runtime-smoke-v3.log').read_text(errors='replace').replace('\0','');mapped=sorted(set(line.split()[-1]for line in text.splitlines()if line.startswith('MAP|')and'/'in line));images=[f for f in mapped if f.endswith('.art')];oats=[f for f in mapped if f.endswith('.oat')];exec_oats=sorted(set(line.split()[-1]for line in text.splitlines()if line.startswith('MAP|')and' r-xp 'in line and line.endswith('.oat')));root=Path('/opt/saildroid/releases/api29-r321j-dev-20261105');expected={str(root/'system/framework/arm64'/name)for name in json.loads((p/'result.json').read_text())['files']if name.endswith('.art')};passed=q.returncode==0 and 'FULL_BOOT_SMOKE=passed|'in text and set(images)==expected and len(exec_oats)==15
result=dict(passed=passed,returncode=q.returncode,seconds=time.monotonic()-start,command=cmd,images=images,oats=oats,executable_oats=exec_oats,expected_image_count=15,exact_image_set=set(images)==expected,hidden_api_denied_bits=3 if 'hidden_api_denied=3'in text else None,ordinary_uid=65534,network_namespace='isolated',legacy_paths_hidden=['/home','/tmp','/var/tmp','/usr/local/lib'],device_accessed=False,scope='ART loading and pure framework/core behavior only; no UI or performance proof',change_from_initial='Use original component SdJavaCommand headless native/bootstrap initialization as16th boot jar, after exact15-image prefix; same compiler output and source bytes')
(p/'runtime-smoke-v3.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in['command','images','oats','executable_oats']},indent=2));assert passed
