from pathlib import Path
import subprocess,os,json,hashlib,time,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'aot-build-v1';out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior=b;meta=json.loads((prior/'overlay.json').read_text());payload=Path(json.loads((prior/'package.json').read_text())['payload']);runtime=json.loads((payload/'runtime.json').read_text());apk=r/'test/qq.apk';assert sha(apk)=='09bf4fe46dea0fcac0f1909f1ef33c6bf390c5f93f2c4a16e0f0768d686b6dc8'
# Reconstruct exactly the phone's immutable runtime inputs, without copying large libraries.
root=out/'root';root.mkdir();predecessor=Path('/var/tmp/saidroid-next-api29-component-r86-web/root');assert predecessor.exists()
needed=runtime['boot_jars']+['lib/runtime.jar','lib/libart.so']+[n for n in meta['install_manifest']['files']if n.startswith('system/framework/')]
sources={}
for n in needed:
 target=root/n;target.parent.mkdir(parents=True,exist_ok=True);sources_to_try=[payload/n,r/'build/evidence/qq-cover-perf306-20261103-v1/payload'/n,Path('/var/tmp/saidroid-native-service-lifecycle305-v1/payload')/n,Path('/var/tmp/saidroid-icmp-cleanup286-v1-formal-vm-component/root')/n];source=next(p for p in sources_to_try if p.is_file()and sha(p)==meta['install_manifest']['files'][n]['sha256'])
 v=meta['install_manifest']['files'][n];assert sha(source)==v['sha256'],n;target.symlink_to(source);sources[n]=dict(path=str(source),sha256=v['sha256'])
for n,target in meta['install_manifest']['symlinks'].items():
 p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(target)
# dex2oat gets the same extended boot classpath and logical locations as the host.
names=runtime['boot_jars']+['lib/runtime.jar'];boot=':'.join(str(root/n)for n in names);locations=':'.join('/home/art/api29-root/'+n for n in names)
location=json.loads((r/'build/evidence/qq-cover-perf306-20261103-v1/inventory.json').read_text())['app']['apk_path'];compiler=Path('/home/art/bin/dex2oat');cmd=[str(compiler),'--host','--instruction-set=arm64','--compiler-filter=speed','-j4','--runtime-arg','-Xmx1536m','--boot-image='+str(root/runtime['boot_image']['path']),'--runtime-arg','-Xbootclasspath:'+boot,'--runtime-arg','-Xbootclasspath-locations:'+locations,'--dex-file='+str(apk),'--dex-location='+location,'--oat-file='+str(out/'base.odex'),'--class-loader-context=PCL[]','--stored-class-loader-context=PCL[]']
env=dict(os.environ,LD_LIBRARY_PATH=str(root/'lib')+':/home/art/lib',ANDROID_ROOT=str(root),ANDROID_DATA=str(out/'data'));(out/'data').mkdir();record=dict(command=cmd,compiler_sha256=sha(compiler),apk_sha256=sha(apk),sources=sources,environment={k:env[k]for k in ['LD_LIBRARY_PATH','ANDROID_ROOT','ANDROID_DATA']},started=time.time());(out/'recipe.json').write_text(json.dumps(record,indent=2)+'\n')
with(out/'compile.log').open('ab',buffering=0)as stream:p=subprocess.run(cmd,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=2400)
record.update(returncode=p.returncode,seconds=time.time()-record['started'],files={n:dict(sha256=sha(out/n),bytes=(out/n).stat().st_size)for n in ['base.odex','base.vdex']if(out/n).is_file()},passed=p.returncode==0);(out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items()if k not in ['sources','command','environment']},indent=2),flush=True);assert record['passed']
