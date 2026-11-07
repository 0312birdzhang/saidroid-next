#!/usr/bin/env python3
"""Create byte-preserving stored/aligned DEX JAR copies. VM-only; no activation."""
import argparse,hashlib,json,platform,struct,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('jars',nargs='+');a=p.parse_args()
assert platform.system()=='Linux' and 'sailfishos' not in Path('/etc/os-release').read_text().lower()
assert not a.output.exists();a.output.mkdir(parents=True);rows=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for relative in a.jars:
 rel=Path(relative);assert not rel.is_absolute()and'..'not in rel.parts and rel.suffix=='.jar'
 source=a.root/rel;dest=a.output/'root'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(source)as original,zipfile.ZipFile(dest,'w')as result:
  for item in original.infolist():
   entry=zipfile.ZipInfo(item.filename,item.date_time);entry.external_attr=item.external_attr;entry.compress_type=zipfile.ZIP_STORED if item.filename.endswith('.dex')else item.compress_type
   if entry.compress_type==zipfile.ZIP_STORED:
    # Well-formed unknown extra field; 0–3 bytes align local payload to four.
    at=result.fp.tell()+30+len(entry.filename.encode())
    padding=(-(at+4))%4;entry.extra=struct.pack('<HH',0xd935,padding)+bytes(padding)
   result.writestr(entry,original.read(item.filename))
 with zipfile.ZipFile(source)as original,zipfile.ZipFile(dest)as result:
  assert original.namelist()==result.namelist()
  details=[]
  for n in original.namelist():
   assert original.read(n)==result.read(n)
   if n.endswith('.dex'):
    i=result.getinfo(n);offset=i.header_offset+30+len(i.filename.encode())+len(i.extra)
    assert i.compress_type==0 and offset%4==0
    details.append(dict(name=n,bytes=i.file_size,crc32=i.CRC,sha256=hashlib.sha256(result.read(n)).hexdigest(),offset=offset))
 dest.chmod(0o644);rows.append(dict(path=relative,before_sha256=sha(source),after_sha256=sha(dest),dex=details,before_bytes=source.stat().st_size,after_bytes=dest.stat().st_size))
r=dict(passed=True,scope='ZIP container only; every entry including encoded DEX byte-identical; no component activation or cache manifest rewrite',jars=rows)
(a.output/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
