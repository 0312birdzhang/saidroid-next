from pathlib import Path
import subprocess,json,hashlib,os
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;out=b/'native-build-v2';out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();java=Path('/tmp/jdkfull/jdk-21.0.13+9');commands=[]
def run(cmd,name):
 commands.append(cmd)
 with(b/(name+'.log')).open('ab',buffering=0)as stream:subprocess.run(cmd,check=True,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
for mode,kind in [('client-header','client-protocol.h'),('private-code','protocol.c')]:
 for n,xml in [('xdg-shell',Path('/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml')),('surface-extension',b/'baseline-source/native/window/surface-extension.xml')]:run(['wayland-scanner',mode,str(xml),str(out/(n+'-'+kind))],'scanner')
flags=subprocess.check_output(['pkg-config','--cflags','--libs','wayland-client','libpng'],text=True).split();sources=['native/window/sdwindow.c','native/hwui/sd-hwui-host.c','native/hwui/sd-hwui-background.c','native/window/sdcontrol.c','native/window/sdactivate.c']
def window(source,name):return ['gcc','-shared','-fPIC','-O2','-Wall','-o',str(out/name),*[str(source/n)for n in sources],str(out/'xdg-shell-protocol.c'),str(out/'surface-extension-protocol.c'),'-I'+str(out),'-I'+str(java/'include'),'-I'+str(java/'include/linux'),*flags,'-pthread','-ldl']
run(window(b/'baseline-source','baseline-window.so'),'window-baseline');expected=json.loads((r/'build/evidence/qq-service-lifecycle305-20261103-v1/bundle/overlay.json').read_text())['install_manifest']['files'];assert sha(out/'baseline-window.so')==expected['lib/libsdwindow.so']['sha256'],sha(out/'baseline-window.so')
run(window(b/'source','libsdwindow.so'),'window-candidate')
old=json.loads((r/'build/evidence/qq-surface-texture300-20261102-v1/native-build.json').read_text());cmd=old['commands'][-1][:];cmd[cmd.index('-o')+1]=str(out/'baseline-host');run(cmd,'host-baseline');assert sha(out/'baseline-host')==expected['libexec/saildroid-host']['sha256']
cmd[cmd.index('-o')+1]=str(out/'saildroid-host');entry=next(v for v in cmd if v.endswith('/host-entry.cpp'));cmd[cmd.index(entry)]=str(b/'source/native/host/host-entry.cpp');run(cmd,'host-candidate')
d=dict(passed=True,baseline_window_byte_identical=True,baseline_host_byte_identical=True,files={n:dict(sha256=sha(out/n),path=str(out/n),bytes=(out/n).stat().st_size)for n in ['libsdwindow.so','saildroid-host']},commands=commands,sources={str(p.relative_to(b/'source')):sha(p)for p in (b/'source').rglob('*')if p.is_file()});(b/'native-build-v2.json').write_text(json.dumps(d,indent=2)+'\n');print('NATIVE306_BUILD=passed',flush=True)
