from pathlib import Path
import subprocess,json,hashlib,os,shutil,time
p=Path(__file__).parent;guard=p.parent/'inotify-budget-analysis-v1';perf=p.parent;out=p/'art-tests';out.mkdir();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
meta=json.loads((p/'build.json').read_text());candidate=p/'candidate.so';assert sha(candidate)==meta['candidate_sha256']
java=json.loads((guard/'java-guard-v3/result.json').read_text());assert java['passed']and java['sources']['GuardJavaProbe.java']==sha(p/'source/GuardJavaProbe.java')
shutil.copytree(guard/'java-guard-v3/dex',out/'dex')
root=perf/'distribution-v10/rpm/extracted/opt/saildroid/releases/api29-r321l-dev-20261105';target='/opt/saildroid/releases/api29-r321l-dev-20261105';base=json.loads((perf/'resource-table-sharing-v1/inotify-vm-v1/result.json').read_text())['command']
oldroot=str(perf/'distribution-v9/rpm/extracted/opt/saildroid/releases/api29-r321l-dev-20261105');oldwork=str(perf/'resource-table-sharing-v1/inotify-vm-v1')
work=Path('/var/tmp/saidroid-no-opath-art321');assert not work.exists();work.mkdir(mode=0o755);smoke=work/'smoke';user=work/'user';smoke.mkdir(mode=0o700);user.mkdir(mode=0o700);os.chown(smoke,65534,65534);os.chown(user,65534,65534);(smoke/'data0').mkdir();os.chown(smoke/'data0',65534,65534)
cmd=[s.replace(oldroot,str(root)).replace(oldwork,str(smoke))for s in base];i=cmd.index('--');cmd[i:i]=['--tmpfs','/run/user','--dir','/run/user/65534','--bind',str(user),'/run/user/65534','--ro-bind',str(out/'dex'),'/var/tmp/smoke/dex','--ro-bind',str(candidate),target+'/lib/libsdhost29.so'];cmd[cmd.index('FileObserverProbe')]='GuardJavaProbe'
start=time.monotonic()
try:
 with(out/'run.log').open('w')as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 log=(out/'run.log').read_text(errors='replace').replace('\0','');markers=[s for s in log.splitlines()if s.startswith('GUARD_JAVA')]
 result={'passed':q.returncode==0 and any(s.startswith('GUARD_JAVA=passed')for s in markers),'returncode':q.returncode,'markers':markers,'seconds':time.monotonic()-start,'command':cmd,'candidate_sha256':sha(candidate),'unchanged_java_probe_sha256':sha(p/'source/GuardJavaProbe.java'),'no_extra_preload':True,'same_path_isolated_library_bind':True,'phone_accessed':False}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='command'}),flush=True);assert result['passed']
finally:shutil.rmtree(work)
