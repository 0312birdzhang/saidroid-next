#!/usr/bin/env python3
"""Store an unsigned framework resources.arsc entry for shared file mapping.

Every decompressed ZIP member is independently compared before publication.
Signed APKs and duplicate members are rejected; this is never an app rewrite.
"""
from pathlib import Path
import argparse,hashlib,json,os,struct,zipfile
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--proof',type=Path,required=True);a=p.parse_args();assert a.source.resolve()!=a.output.resolve()and not a.output.exists()and not a.proof.exists()
sha=lambda data:hashlib.sha256(data).hexdigest();raw=a.source.read_bytes();assert b'APK Sig Block 42'not in raw,'APK signing block present'
a.output.parent.mkdir(parents=True,exist_ok=True);temporary=a.output.with_name(a.output.name+'.pending');assert not temporary.exists()
with zipfile.ZipFile(a.source)as source:
 infos=source.infolist();names=[i.filename for i in infos];assert len(names)==len(set(names))and 'resources.arsc'in names;assert not any(n.upper().startswith('META-INF/')and n.upper().endswith(('.RSA','.DSA','.EC','.SF'))for n in names),'Signed archive rejected'
 expected={};offsets={}
 try:
  with zipfile.ZipFile(temporary,'w',allowZip64=False)as dest:
   dest.comment=source.comment
   for old in infos:
    data=source.read(old);expected[old.filename]=dict(bytes=len(data),sha256=sha(data));info=zipfile.ZipInfo(old.filename,old.date_time)
    for key in ['comment','extra','create_system','create_version','extract_version','reserved','volume','internal_attr','external_attr']:setattr(info,key,getattr(old,key))
    info.compress_type=zipfile.ZIP_STORED if old.filename=='resources.arsc'else old.compress_type
    if old.filename=='resources.arsc':
     start=dest.fp.tell()+30+len(info.filename.encode('utf-8'))+len(info.extra);pad=(-start)%4096
     if 0<pad<4:pad+=4096
     if pad:info.extra+=struct.pack('<HH',0xd935,pad-4)+bytes(pad-4)
    dest.writestr(info,data)
  with zipfile.ZipFile(temporary)as check:
   actual={i.filename:dict(bytes=i.file_size,sha256=sha(check.read(i)))for i in check.infolist()};assert actual==expected;assert check.comment==source.comment;assert check.testzip()is None
   entry=check.getinfo('resources.arsc');assert entry.compress_type==zipfile.ZIP_STORED
  with temporary.open('rb')as stream:
   stream.seek(entry.header_offset);header=stream.read(30);signature,version,flags,method=struct.unpack_from('<IHHH',header);nl,xl=struct.unpack_from('<HH',header,26);offset=entry.header_offset+30+nl+xl;assert signature==0x04034b50 and method==0 and offset%4096==0
   stream.seek(offset);assert sha(stream.read(entry.file_size))==expected['resources.arsc']['sha256']
  with temporary.open('rb')as stream:os.fsync(stream.fileno())
  os.replace(temporary,a.output)
 except BaseException:
  if temporary.exists():temporary.unlink()
  raise
proof=dict(passed=True,source=str(a.source),source_sha256=sha(raw),source_bytes=len(raw),output=str(a.output),output_sha256=sha(a.output.read_bytes()),output_bytes=a.output.stat().st_size,members_identical=True,members=len(expected),resources=expected['resources.arsc'],resources_compressed_before=source.getinfo('resources.arsc').compress_size,resources_compression_before=source.getinfo('resources.arsc').compress_type,resources_compression_after=0,resources_data_offset=offset,alignment=4096,member_manifest=expected,scope='ZIP encoding only, unsigned framework APK, every decompressed member unchanged; device mapping/CPU/memory benefit unclaimed')
a.proof.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k!='member_manifest'}),flush=True)
