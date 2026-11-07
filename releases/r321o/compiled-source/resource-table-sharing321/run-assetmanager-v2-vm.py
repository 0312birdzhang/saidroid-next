from pathlib import Path
import subprocess,hashlib,json,os,time,signal,zipfile,stat
p=Path(__file__).parent;perf=p.parent;repo=perf.parents[3];out=p/'assetmanager-vm-v2';assert not out.exists();out.mkdir();source=perf/'distribution-v9/rpm/extracted/opt/saildroid/releases/api29-r321l-dev-20261105';root='/opt/saildroid/releases/api29-r321l-dev-20261105';sha=lambda f:hashlib.file_digest(f.open('rb'),'sha256').hexdigest();proof=json.loads((p/'repack-proof.json').read_text());original=source/'system/framework/framework-res.apk';stored=p/'framework-res-stored.apk';assert sha(original)==proof['source_sha256']and sha(stored)==proof['output_sha256'];assert proof['members_identical']
with zipfile.ZipFile(original)as a,zipfile.ZipFile(stored)as b:
 assert a.namelist()==b.namelist()
 for n in a.namelist():assert hashlib.sha256(a.read(n)).digest()==hashlib.sha256(b.read(n)).digest(),n
out.chmod(0o755);classes=out/'classes';dex=out/'dex';classes.mkdir();dex.mkdir();jdk=Path('/tmp/jdkfull/jdk-21.0.13+9/bin');android=repo/'build/codex-api29/inputs/android-all-10-robolectric-5803371.jar';subprocess.run([str(jdk/'javac'),'--release','8','-cp',str(android),'-d',str(classes),str(p/'ResourceTableProbe.java')],check=True)
subprocess.run([str(jdk/'java'),'-cp',str(repo/'build/codex-api29/inputs/r8-8.3.37.jar'),'com.android.tools.r8.D8','--min-api','29','--lib',str(android),'--output',str(dex),str(classes/'ResourceTableProbe.class')],check=True)
for f in [dex,*dex.iterdir()]:f.chmod(0o755 if f.is_dir()else 0o644)
old=json.loads((perf/'full-boot-preloaded-v1/runtime-smoke-v1.json').read_text())['command'];oldroot='/opt/saildroid/releases/api29-r321j-dev-20261105';cmd=[s.replace(oldroot,root)for s in old]
# Replace original J assembly+L image overlay with the final extractedL root, preserving actual CLI bootstrap/policy.
pos=cmd.index('--ro-bind',cmd.index('--dir')+1);assert cmd[pos+2]==root;cmd[pos+1]=str(source)
for i in range(len(cmd)-2):
 if cmd[i]=='--ro-bind'and cmd[i+2]==root+'/system/framework/arm64':del cmd[i:i+3];break
workpos=cmd.index('--bind');assert cmd[workpos+2]=='/var/tmp/smoke';cmd[workpos+1]=str(out);cmd[-1]='ResourceTableProbe'
rows=[]
for label,apk in [('compressed',original),('stored',stored)]:
 run=out/label;run.mkdir();run.chmod(0o777);children=[];start=time.monotonic()
 try:
  for i in range(2):
   name='process'+str(i);data=run/('data'+str(i));data.mkdir();data.chmod(0o777);launch=list(cmd);launch=[s.replace('ANDROID_DATA=/var/tmp/smoke/data','ANDROID_DATA=/var/tmp/smoke/'+label+'/data'+str(i))for s in launch]
   pos=launch.index('--');launch[pos:pos]=['--dir','/home/art','--symlink',root,'/home/art/api29-root','--ro-bind',str(apk),root+'/system/framework/framework-res.apk'];launch+=['/var/tmp/smoke/'+label,name];log=(run/(name+'.log')).open('wb');child=subprocess.Popen(launch,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append((name,child,log,launch))
  deadline=time.monotonic()+45
  while not all((run/(name+'-ready')).exists()for name,_,_,_ in children):
   assert time.monotonic()<deadline,'ready timeout'
   assert all(child.poll()is None for _,child,_,_ in children),'child exited before ready'
   time.sleep(.05)
  (run/'capture').write_text('capture both concurrently loaded resources\n')
  while not all((run/(name+'-captured')).exists()for name,_,_,_ in children):
   assert time.monotonic()<deadline,'capture timeout';time.sleep(.05)
  (run/'finish').write_text('finish\n')
  for name,child,log,launch in children:
   code=child.wait(timeout=10);log.close();text=(run/(name+'.log')).read_text(errors='replace');assert code==0 and 'RESOURCE_TABLE_PROBE=passed|'in text,text[-3000:];rows.append(dict(label=label,process=name,returncode=code,command=launch,values_sha256=sha(run/(name+'-values.txt')),ready=(run/(name+'-ready')).read_text(),smaps=str(run/(name+'-after.smaps'))))
 finally:
  for name,child,log,_ in children:
   if child.poll()is None:os.killpg(child.pid,signal.SIGTERM)
  for name,child,log,_ in children:
   try:child.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
   log.close()
assert len({v['values_sha256']for v in rows})==1;assert sha(original)==proof['source_sha256']and sha(stored)==proof['output_sha256'];result=dict(passed=True,scope='Actual extracted L ART+Android AssetManager through public Resources APIs, two concurrent ordinary UID65534 processes per encoding; no UI or phone',rows=rows,original_sha256=sha(original),stored_sha256=sha(stored),native_unchanged=True,hidden_api_unchanged=True,all_decompressed_members_independently_rehashed=True,device_accessed=False)
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
