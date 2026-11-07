from pathlib import Path
import json,hashlib,copy,shutil
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;prior=r/'build/evidence/qq-media-player312-20261103-v1/v9';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=json.loads((prior/'overlay.json').read_text());meta=copy.deepcopy(old);after=meta['install_manifest'];payload=b/'payload';payload.mkdir();updated=[];build=json.loads((b/'encoded-build-v1.json').read_text());assert build['passed']
def install(p,n,mode=0o644):
 q=payload/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(mode);after['files'][n]=meta['changes'][n]=dict(sha256=sha(q),size=q.stat().st_size,mode=mode);updated.append(n)
install(Path(build['encoded_root'])/'lib/runtime.jar','lib/runtime.jar')
for p in (r/'scripts/api29/runtime-permission-compat').rglob('*'):
 if p.is_file():install(p,'share/build/runtime-permission313/'+str(p.relative_to(r/'scripts/api29/runtime-permission-compat')))
for n in ['build-runtime-vm.py','runtime-build-v1.json','encode-runtime-vm.py','encoded-build-v1.json','package-vm.py']:install(b/n,'share/build/runtime-permission313/'+n)
install(r/'native/media/droid-camera/SdCamera.java','share/build/droid-camera313/SdCamera.java')
install(r/'native/media/gstreamer-player/SdMediaPlayer.java','share/build/droid-camera313/SdMediaPlayer.java')
for p in (r/'native/media/droid-camera').rglob('*'):
 if p.is_file()and '__pycache__'not in str(p):install(p,'share/build/droid-camera313/source/'+str(p.relative_to(r/'native/media/droid-camera')))
for name,target in [('libsdcamera-host.so','lib/libsdcamera-host.so'),('sdcamera-helper','libexec/sdcamera-helper')]:install(b.parent/'camera-native-build-v12'/name,target,0o755)
install(b.parent/'camera-native-build-v12/manifest.json','share/build/droid-camera313/native-manifest.json')
for p in (r/'scripts/api29/webview-history-compat').rglob('*'):
 if p.is_file():install(p,'share/build/webview-history313/'+str(p.relative_to(r/'scripts/api29/webview-history-compat')))
for p in (r/'native/webview/qt-helper').iterdir():
 if p.is_file():install(p,'share/build/webview-history313/native/'+p.name)
install(r/'native/media/gstreamer-player/SdAudio.java','share/build/droid-camera313/SdAudio.java')
install(b.parent/'webview-history-native-v2/sdwebviewd','libexec/sdwebviewd',0o755)
install(b.parent/'webview-history-native-v2.json','share/build/webview-history313/native-manifest.json')
install(b.parent/'v24/frame-native/libsdhost29.so','lib/libsdhost29.so')
for p in (r/'scripts/api29/surface-view-compat').rglob('*'):
 if p.is_file():install(p,'share/build/surface-view313/'+str(p.relative_to(r/'scripts/api29/surface-view-compat')))
for p in (b.parent/'v24/frame-native').rglob('*'):
 if p.is_file()and(p.suffix in ['.json','.c','.h']):install(p,'share/build/surface-view313/native/'+str(p.relative_to(b.parent/'v24/frame-native')))
install(b/'build-frame-host-vm.py','share/build/surface-view313/build-frame-host-vm.py')
install(b/'window-native/libsdwindow.so','lib/libsdwindow.so')
for p in (b/'window-native/source').rglob('*'):
 if p.is_file():install(p,'share/build/surface-view313/window-source/'+str(p.relative_to(b/'window-native/source')))
install(b/'window-native/manifest.json','share/build/surface-view313/window-manifest.json')
install(b/'build-window-native-vm.py','share/build/surface-view313/build-window-native-vm.py')
install(Path(__file__),'share/build/surface-view313/package-vm.py')
after['bytes']=sum(v['size']for v in after['files'].values());(b/'overlay.json').write_text(json.dumps(meta,indent=2)+'\n');(b/'package.json').write_text(json.dumps(dict(passed=True,payload=str(payload),updated_files=updated,files=len(after['files']),symlinks=len(after['symlinks']),manifest_sha256=hashlib.sha256((json.dumps(after,indent=2)+'\n').encode()).hexdigest()),indent=2)+'\n');print('PERMISSION313_PACKAGE=passed|files='+str(len(after['files'])),flush=True)
