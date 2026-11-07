from pathlib import Path
import json,hashlib,subprocess,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'process-runtime-v2';out.mkdir();prior=b.parent/'wechat-startup320-20261104';base=prior/'runtime-build-v4/classes';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();fw=r/'build/codex-api29/inputs/android-all-10-robolectric-5803371.jar';jdk=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');before={str(p.relative_to(base)):sha(p)for p in base.rglob('*.class')};assert before==json.loads((prior/'runtime-build-v4.json').read_text())['classfiles_after'];commands=[]
def run(cmd,log):
 commands.append(list(map(str,cmd)))
 with(out/log).open('ab',buffering=0)as f:subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
module=r/'scripts/api29/component-process-info-compat';old=out/'baseline-check';old.mkdir();run([jdk/'javac','--release','8','-nowarn','-cp',str(fw)+':'+str(base),'-d',old,module/'baseline/SdApkPackage.java'],'baseline.log');assert all(before[str(p.relative_to(old))]==sha(p)for p in old.rglob('*.class')),'Baseline Java class differs'
new=out/'overlay';new.mkdir();run([jdk/'javac','--release','8','-nowarn','-cp',str(fw)+':'+str(base),'-d',new,module/'source/SdApkPackage.java'],'javac.log');classes=out/'classes';shutil.copytree(base,classes)
for p in new.rglob('*.class'):shutil.copyfile(p,classes/p.relative_to(new))
after={str(p.relative_to(classes)):sha(p)for p in classes.rglob('*.class')};changed=[n for n in before if before[n]!=after[n]];assert changed==['SdApkPackage.class'];assert after.keys()==before.keys()
run([jdk/'java','-Xmx2g','-cp',r/'build/codex-api29/inputs/r8-8.3.37.jar','com.android.tools.r8.D8','--release','--min-api','29','--lib',fw,'--output',out/'runtime.jar',*sorted(classes.rglob('*.class'))],'d8.log');record=dict(passed=True,classfiles_before=before,classfiles_after=after,changed_classfiles=changed,runtime_sha256=sha(out/'runtime.jar'),commands=commands);(b/'process-runtime-build-v2.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(passed=True,changed=changed)))
