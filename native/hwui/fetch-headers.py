#!/usr/bin/env python3
"""Fetch the private, pinned Android native build inputs; no system installs."""
from pathlib import Path
import argparse,base64,concurrent.futures,hashlib,io,json,re,subprocess,tarfile,time,urllib.request
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
base=a.output;root=base/'headers';root.mkdir(parents=True,exist_ok=True)
tag='android-10.0.0_r47';vndk='5f9884aa352825291757dfd6694b874ad8c1805e';libcxx='d356ee1683aa5681564c81ad69fe19bc6abd5da5'
sources={
 'gui':('frameworks/native','libs/gui/include'),'ui':('frameworks/native','libs/ui/include'),
 'nativewindow':('frameworks/native','libs/nativewindow/include'),'nativebase':('frameworks/native','libs/nativebase/include'),
 'binder':('frameworks/native','libs/binder/include'),'math':('frameworks/native','libs/math/include'),
 'arect':('frameworks/native','libs/arect/include'),'opengl':('frameworks/native','opengl/include'),
 'libutils':('system/core','libutils/include'),'liblog':('system/core','liblog/include'),
 'libcutils':('system/core','libcutils/include'),'libsystem':('system/core','libsystem/include'),
 'libbacktrace':('system/core','libbacktrace/include'),'libbase':('system/core','base/include'),
 'libhardware':('hardware/libhardware','include'),'sync':('system/core','libsync/include'),
 'hidlbase':('system/libhidl','base/include'),'hidltransport':('system/libhidl','transport/include'),
 'hybrid':('system/libhidl','transport/token/1.0/utils/include'),
 'bionic':('bionic','libc/include'),'kernel':('bionic','libc/kernel/uapi'),
 'kernelarm64':('bionic','libc/kernel/uapi/asm-arm64')}
def download(url):
 for attempt in range(4):
  try:return urllib.request.urlopen(url,timeout=45).read()
  except Exception:
   if attempt==3:raise
   time.sleep(1+attempt)
def archive(item):
 name,(repo,path)=item;target=root/name;stamp=target/'.source.json'
 info=dict(repo=repo,path=path,revision=tag)
 if stamp.is_file() and json.loads(stamp.read_text())==info:return name+' cached'
 data=download(f'https://android.googlesource.com/platform/{repo}/+archive/{tag}/{path}.tar.gz')
 target.mkdir(exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as package:package.extractall(target,filter='data')
 stamp.write_text(json.dumps(info)+'\n');return name+' verified source'
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for result in pool.map(archive,sources.items()):print(result,flush=True)
# The small Android-specific kernel overlay is not consistently served by the
# archive endpoint. Fetch its two exported compiler headers individually.
for name in ['compiler.h','compiler_types.h']:
 target=root/'kernelandroid/linux'/name;target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(base64.b64decode(download(f'https://android.googlesource.com/platform/bionic/+/{tag}/libc/kernel/android/uapi/linux/{name}?format=TEXT')))
checkout=base/'libcxx-source'
if not checkout.exists():subprocess.run(['git','clone','--depth','1','--branch',tag,'https://android.googlesource.com/platform/external/libcxx',str(checkout)],check=True)
assert subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()==libcxx
# HIDL's versioned interfaces are stable. These generated 1.0/1.1/1.2/2.0
# declarations come from one immutable VNDK snapshot; no generated code is linked.
queue=['android/hardware/graphics/common/1.1/types.h','android/hardware/graphics/common/1.2/types.h','android/hardware/graphics/bufferqueue/1.0/IGraphicBufferProducer.h','android/hardware/graphics/bufferqueue/2.0/IGraphicBufferProducer.h'];seen=set()
while queue:
 name=queue.pop(0)
 if name in seen:continue
 seen.add(name);parts=name.split('/');version=parts[-2]
 repo='hardware/interfaces' if parts[1]=='hardware' else 'system/libhidl/transport'
 module='.'.join(parts[:-2])+'@'+version+'_genc++_headers'
 path='/'.join([repo,*parts[2:-2],version,module,'gen',name])
 target=root/'generated'/name;target.parent.mkdir(parents=True,exist_ok=True)
 data=base64.b64decode(download(f'https://android.googlesource.com/platform/prebuilts/vndk/v30/+/{vndk}/arm64/include/generated-headers/{path}?format=TEXT'));target.write_bytes(data)
 queue.extend(re.findall(r'#include <(android/(?:hidl|hardware)/[^>]+)>',data.decode()))
record=dict(android_revision=tag,libcxx_commit=libcxx,generated_headers_commit=vndk,
 files={str(f.relative_to(base)):hashlib.sha256(f.read_bytes()).hexdigest()for f in sorted(root.rglob('*')) if f.is_file()})
(base/'input-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print('HWUI_HEADERS=ready|files='+str(len(record['files'])))
