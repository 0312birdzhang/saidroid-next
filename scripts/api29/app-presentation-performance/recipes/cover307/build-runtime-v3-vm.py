from pathlib import Path
import os,subprocess,hashlib,json,shutil,zipfile,importlib.util
os.umask(0o022)
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;base=Path('/var/tmp/saidroid-service-lifecycle305-runtime-v1');out=b/'runtime-build-v3';out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=b/'source';java=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');fw=r/'build/codex-api29/inputs/android-all-10-robolectric-5803371.jar';r8=r/'build/codex-api29/inputs/r8-8.3.37.jar';commands=[]
before={str(p.relative_to(base/'classes')):sha(p)for p in (base/'classes').rglob('*.class')};assert before==json.loads((r/'build/evidence/qq-service-lifecycle305-20261103-v1/runtime-build.json').read_text())['classfiles_after']
def run(cmd,n):
 commands.append(cmd)
 with(out/n).open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
old=out/'baseline-classes';old.mkdir();run([str(java/'javac'),'--release','8','-nowarn','-cp',str(fw)+':'+str(base/'classes'),'-d',str(old),str(r/'build/evidence/qq-surface-texture300-20261102-v1/source/scripts/device/SdWindowHost.java')],'baseline-javac.log');assert all(before[str(p.relative_to(old))]==sha(p)for p in old.rglob('*.class'))
new=out/'overlay-classes';new.mkdir();sources=sorted((source/'scripts/device').glob('*.java'));run([str(java/'javac'),'--release','8','-nowarn','-cp',str(fw)+':'+str(base/'classes'),'-d',str(new),*map(str,sources)],'javac.log')
classes=out/'classes';shutil.copytree(base/'classes',classes)
for p in new.rglob('*.class'):shutil.copyfile(p,classes/p.relative_to(new))
after={str(p.relative_to(classes)):sha(p)for p in classes.rglob('*.class')};changed=[n for n in before if before[n]!=after[n]];added=sorted(set(after)-set(before));assert all(n=='SdWindowHost.class'or n.startswith('SdWindowHost$')for n in changed),changed;assert all(n.startswith('SdCoverSnapshot')or n.startswith('SdWindowHost$')for n in added),added
run([str(java/'java'),'-Xmx2g','-cp',str(r8),'com.android.tools.r8.D8','--release','--min-api','29','--lib',str(fw),'--output',str(out/'runtime.jar'),*map(str,sorted(classes.rglob('*.class')))],'d8.log')
record=dict(passed=True,scope='One HWUI render-tree cover snapshot per real background transition. Steady-state app rendering and lifecycle unchanged.',builder_sha256=sha(Path(__file__)),source_sha256={str(p.relative_to(source)):sha(p)for p in sources},classfiles_before=before,classfiles_after=after,baseline_classfiles_reproduced=True,changed_classfiles=changed,added_classfiles=added,runtime_sha256=sha(out/'runtime.jar'),commands=commands)
(b/'runtime-build-v3.json').write_text(json.dumps(record,indent=2)+'\n');print('RUNTIME307_BUILD=passed',flush=True)
