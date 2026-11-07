from pathlib import Path
import subprocess,shutil,json,hashlib,re
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=Path(__file__).parent;prior=Path('/var/tmp/saidroid-linker-cfi-owner-20261031');out=Path('/var/tmp/saidroid-linker-thread-errors310-v3');out.mkdir();source=out/'source';shutil.copytree(prior/'source',source,ignore=shutil.ignore_patterns('.git','builddir','__pycache__'),symlinks=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();inputs={str(p.relative_to(source)):sha(p)for p in source.rglob('*')if p.is_file()and not p.is_symlink()};commands=[]
def run(cmd,n):
 commands.append(cmd)
 with(out/n).open('ab',buffering=0)as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
build=out/'build';run(['meson','setup',str(build),str(source)],'meson.log');run(['ninja','-C',str(build),'libdl_bio.so.0.0.1'],'baseline.log');shutil.copyfile(build/'libdl_bio.so.0.0.1',out/'baseline.so');assert sha(prior/'libdl_bio.so.0')=='1d1b2929d531512e27c3e2457039a82aa9ec3c6169a3963e69bdd6018b46a135'
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

p=source/'linker/dlfcn.c';before=p.read_text();assert 'static char dl_err_buf[1024];\nstatic const char *dl_err_str;'in before
p.write_text(before.replace('static char dl_err_buf[1024];\nstatic const char *dl_err_str;','''/* dlerror is thread-local and consumed once. A process-global pending
 * pointer lets another loader thread clear it before ART reads its own error. */
static __thread char dl_err_buf[1024];
static __thread const char *dl_err_str;'''))
run(['ninja','-C',str(build),'libdl_bio.so.0.0.1'],'candidate.log');shutil.copyfile(build/'libdl_bio.so.0.0.1',out/'libdl_bio.so.0')
def signatures(p):
 result=[]
 for line in subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True).splitlines():
  a=line.split()
  if len(a)>=8 and a[4]in ['GLOBAL','WEAK']:result.append((a[3],a[4],a[5],a[6]=='UND',a[7]))
 return set(result)
a=signatures(out/'baseline.so');z=signatures(out/'libdl_bio.so.0');assert not a-z;assert all(v[3]and v[4].startswith('__tls_get_addr')for v in z-a),z-a
s=b/'source';s.mkdir();shutil.copyfile(p,s/'dlfcn.c');
import difflib
(s/'dlfcn.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile='a/linker/dlfcn.c',tofile='b/linker/dlfcn.c')))
record=dict(passed=True,scope='Thread-local dlerror pending pointer and storage; no load success/error/verification policy changed.',baseline_loaded_sections_byte_identical=True,baseline_debug_directory_only_difference=True,path=str(out/'libdl_bio.so.0'),sha256=sha(out/'libdl_bio.so.0'),source_before=inputs,changed_file='linker/dlfcn.c',source_after_sha256=sha(p),exported_abi_unchanged=True,new_imports=[v[4]for v in z-a],commands=commands);(b/'native-build-v3.json').write_text(json.dumps(record,indent=2)+'\n');print('LINKER310_BUILD=passed',flush=True)
