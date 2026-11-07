from pathlib import Path
import subprocess,shutil,json,hashlib,re
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;prior=Path('/var/tmp/saidroid-linker-segment321-v1');out=Path('/var/tmp/saidroid-linker-domain321-v2');out.mkdir();source=out/'source';shutil.copytree(prior/'source',source,ignore=shutil.ignore_patterns('.git','builddir','__pycache__'),symlinks=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();inputs={str(p.relative_to(source)):sha(p)for p in source.rglob('*')if p.is_file()and not p.is_symlink()};commands=[]
def run(cmd,n):
 commands.append(cmd)
 with(out/n).open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
build=out/'build';run(['meson','setup',str(build),str(source)],'meson.log');run(['ninja','-C',str(build),'libdl_bio.so.0.0.1'],'baseline.log');shutil.copyfile(build/'libdl_bio.so.0.0.1',out/'baseline.so');assert sha(prior/'libdl_bio.so.0')==json.loads((b/'linker-segment-build-v1.json').read_text())['sha256']
# DWARF compilation directory and its build ID vary with this private source path.
# Every loaded section, including relocations, must reproduce the installed linker.
import struct
def loaded_sections(p):
 data=p.read_bytes();off=struct.unpack_from('<Q',data,40)[0];size,count,names=struct.unpack_from('<HHH',data,58);entries=[struct.unpack_from('<IIQQQQIIQQ',data,off+i*size)for i in range(count)];st=entries[names];strings=data[st[4]:st[4]+st[5]];result={}
 for v in entries:
  name=strings[v[0]:].split(b'\0',1)[0].decode()
  if v[2]&2 and name!='.note.gnu.build-id':result[name]=(v[1],v[2],v[3],v[5],data[v[4]:v[4]+v[5]]if v[1]!=8 else b'')
 return result
assert loaded_sections(out/'baseline.so')==loaded_sections(prior/'libdl_bio.so.0'),'Executable/data/relocation baseline differs'

import importlib.util,difflib
spec=importlib.util.spec_from_file_location('origin_patch',r/'native/compat/linker-android-namespace/patch.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
p=source/'linker/linker.c';before=p.read_text();p.write_text(module.patch(before));run(['ninja','-C',str(build),'libdl_bio.so.0.0.1'],'candidate.log');shutil.copyfile(build/'libdl_bio.so.0.0.1',out/'libdl_bio.so.0')
(b/'domain321-v2.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile='a/linker/linker.c',tofile='b/linker/linker.c')))
record=dict(passed=True,path=str(out/'libdl_bio.so.0'),sha256=sha(out/'libdl_bio.so.0'),baseline_loaded_sections_byte_identical=True,source_before=inputs,changed_file='linker/linker.c',source_after_sha256=sha(p),commands=commands);(b/'linker-domain-build-v2.json').write_text(json.dumps(record,indent=2)+'\n');print('DOMAIN321_BUILD=passed',flush=True)
