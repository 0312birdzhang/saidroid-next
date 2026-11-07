from pathlib import Path
import json,hashlib,copy,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;prior=r/'build/evidence/qq-video-ime311-20261103-v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=json.loads((prior/'overlay.json').read_text());meta=copy.deepcopy(old);before=old['install_manifest'];after=meta['install_manifest'];payload=b/'payload-v2';payload.mkdir();updated=[];build=json.loads((b/'encoded-build-v1.json').read_text());assert build['passed'];assert sha(Path(build['encoded_root'])/'lib/runtime.jar')==build['encoded_runtime_sha256']
def install(p,n):
 q=payload/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(0o644);v=dict(sha256=sha(q),size=q.stat().st_size,mode=0o644);after['files'][n]=meta['changes'][n]=v;updated.append(n)
install(Path(build['encoded_root'])/'lib/runtime.jar','lib/runtime.jar')
native=json.loads((b/'native-build-v1.json').read_text());assert native['passed']and sha(Path(native['output']))==native['sha256'];install(Path(native['output']),'lib/libsdmediaplayer-host.so')
for p in (r/'native/media/gstreamer-player').glob('*'):
 if p.is_file():install(p,'share/build/media-player312/native/'+p.name)
for n in ['runtime-build-v1.json','encoded-build-v1.json','build-runtime-vm.py','encode-runtime-vm.py','package-vm.py','native-build-v1.json','native-methods.json']:install(b/n,'share/build/media-player312/'+n)
for p in (b/'source').rglob('*'):
 if p.is_file():install(p,'share/build/media-player312/'+str(p.relative_to(b)))
for p in (r/'scripts/api29/activity-finish-compat').rglob('*'):
 if p.is_file():install(p,'share/build/media-player312/activity-finish/'+str(p.relative_to(r/'scripts/api29/activity-finish-compat')))
runtime=json.loads((prior/'payload/runtime.json').read_text());runtime['media_player']=dict(schema='saidroid-gstreamer-media-player-v1',backend='gstreamer',surface='android-bufferqueue',runtime_sha256=build['encoded_runtime_sha256']);tmp=b/'runtime.json';tmp.write_text(json.dumps(runtime,indent=2)+'\n');install(tmp,'runtime.json');after['bytes']=sum(v['size']for v in after['files'].values());meta['media_player312']=dict(updated_files=updated,scope='GStreamer MediaPlayer JNI; unchanged native baseline plus one private library; framework/core/boot unchanged from r311.');assert before['symlinks']==after['symlinks'];assert all(after['files'][n]==v for n,v in before['files'].items()if n not in updated)
(b/'overlay.json').write_text(json.dumps(meta,indent=2)+'\n');record=dict(passed=True,candidate='r312i',payload=str(payload),updated_files=updated,files=len(after['files']),symlinks=len(after['symlinks']),copied_bytes=sum((payload/n).stat().st_size for n in updated),install_manifest_sha256=hashlib.sha256((json.dumps(after,indent=2)+'\n').encode()).hexdigest(),overlay_sha256=sha(b/'overlay.json'),scope='Candidate only; not accepted.');(b/'package.json').write_text(json.dumps(record,indent=2)+'\n');print('PACKAGE312=passed|files='+str(record['files'])+'|manifest='+record['install_manifest_sha256'],flush=True)
