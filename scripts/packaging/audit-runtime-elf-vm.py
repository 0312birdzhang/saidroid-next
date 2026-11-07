#!/usr/bin/env python3
"""Inspect active component ELF files, their actual dependency resolution and fixed paths."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess

p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--no-legacy-fallback',action='store_true');a=p.parse_args()
assert not a.output.exists()
env=dict(PATH='/usr/bin:/bin',LC_ALL='C',LD_LIBRARY_PATH=str(a.root/'lib')+(''if a.no_legacy_fallback else ':/home/art/lib'))
cache={};entries={};external={};missing=set()
for folder in ['bin','lib','libexec','android-libs']:
 for file in sorted((a.root/folder).rglob('*')):
  if not file.is_file():continue
  with file.open('rb')as f:magic=f.read(4)
  if magic!=b'\x7fELF':continue
  sha=hashlib.sha256(file.read_bytes()).hexdigest()
  if sha not in cache:
   dyn=subprocess.check_output(['readelf','-dW',str(file)],text=True,stderr=subprocess.DEVNULL)
   ver=subprocess.check_output(['readelf','-VW',str(file)],text=True,stderr=subprocess.DEVNULL)
   sym=subprocess.check_output(['readelf','--dyn-syms','--wide',str(file)],text=True,stderr=subprocess.DEVNULL)
   needed=re.findall(r'\(NEEDED\).*\[([^]]+)\]',dyn)
   host='libc.so.6'in needed or 'GLIBC_'in ver
   paths=re.findall(r'\((RPATH|RUNPATH)\).*\[([^]]*)\]',dyn)
   strings=subprocess.check_output(['strings','-a',str(file)],text=True,errors='replace')
   fixed=sorted(set(re.findall(r'/home/art/[A-Za-z0-9_./+:-]*',strings)))
   source=dict(sha256=sha,host_glibc=host,needed=needed,search_paths=paths,fixed_art_paths=fixed,
               undefined=[l.strip()for l in sym.splitlines()if re.search(r'\bUND\b',l)])
   cache[sha]=source
  entry=dict(cache[sha]);relative=str(file.relative_to(a.root))
  if entry['host_glibc']:
   q=subprocess.run(['ldd',str(file)],env=env,capture_output=True,text=True,timeout=20)
   entry['ldd_returncode']=q.returncode;entry['ldd']=q.stdout+q.stderr
   for line in q.stdout.splitlines():
    if 'not found'in line:missing.add(line.strip())
    match=re.match(r'\s*(\S+) => (/\S+)',line)
    if match:
     soname,path=match.groups();real=str(Path(path).resolve())
     if not path.startswith((str(a.root)+'/', '/lib/','/usr/lib/')):
      external.setdefault(soname,dict(paths=[],required_by=[]))
      if real not in external[soname]['paths']:external[soname]['paths'].append(real)
      external[soname]['required_by'].append(relative)
  entries[relative]=entry
out=dict(root=str(a.root),environment=env,entries=entries,external_non_os=external,unresolved=sorted(missing),
         elf_files=len(entries),unique_elf=len(cache),host_glibc=sum(v['host_glibc']for v in entries.values()),
         scope='Host library resolution plus static Android ELF inventory; no application launched')
a.output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k]for k in ['elf_files','unique_elf','host_glibc','external_non_os','unresolved']},indent=2))
