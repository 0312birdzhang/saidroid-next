"""Bounded official API29 CTS input access with a cached remote ZIP index."""
from pathlib import Path
import concurrent.futures,hashlib,json,struct,urllib.request,zlib,time,threading,os,fcntl
URL='https://dl.google.com/dl/android/cts/android-cts-10_r16-linux_x86-arm.zip'
class Archive:
 def __init__(self,index):
  self.index=Path(index);self.index.parent.mkdir(parents=True,exist_ok=True)
  if self.index.exists():self.value=json.loads(self.index.read_text())
  else:
   import io,zipfile
   with urllib.request.urlopen(urllib.request.Request(URL,headers={'Range':'bytes=-65536'}),timeout=40)as r:
    assert r.status==206;total=int(r.headers['Content-Range'].split('/')[-1]);tail=r.read(65537)
   o=tail.rfind(b'PK\x05\x06');_,disk,cdisk,n,nt,size,offset,comment=struct.unpack_from('<4s4H2IH',tail,o);assert disk==cdisk==0 and n==nt and nt<65535
   central=self.get(offset,offset+size-1);end=struct.pack('<4s4H2IH',b'PK\x05\x06',0,0,nt,nt,size,0,0);infos=zipfile.ZipFile(io.BytesIO(central+end)).infolist()
   self.value=dict(url=URL,bytes=total,entries={i.filename:dict(offset=i.header_offset,bytes=i.file_size,compressed=i.compress_size,compression=i.compress_type,crc=i.CRC)for i in infos});self.index.write_text(json.dumps(self.value)+'\n')
  assert self.value['url']==URL;self.entries=self.value['entries']
 def get(self,start,end):
  for attempt in range(4):
   try:
    with urllib.request.urlopen(urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}'}),timeout=40)as r:
     assert r.status==206 and r.headers['Content-Range'].startswith(f'bytes {start}-{end}/');b=r.read(end-start+2);assert len(b)==end-start+1;return b
   except (OSError,AssertionError):
    if attempt==3:raise
    time.sleep(1)
 def extract(self,name,target):
  target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
  with target.with_suffix(target.suffix+'.lock').open('a+b')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   return self._extract_unlocked(name,target)
 def _extract_unlocked(self,name,target):
  info=self.entries[name];target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
  if target.is_file()and target.stat().st_size==info['bytes']:
   crc=0
   with target.open('rb')as f:
    while b:=f.read(1024*1024):crc=zlib.crc32(b,crc)
   if crc==info['crc']:return self.metadata(name,target)
  header=self.get(info['offset'],info['offset']+29);fields=struct.unpack('<4s5H3I2H',header);assert fields[0]==b'PK\x03\x04';start=info['offset']+30+fields[-2]+fields[-1];end=start+info['compressed']-1
  assert info['bytes']<650*1024*1024 and info['compression']in[0,8]
  pending=target.with_suffix(target.suffix+'.partial')
  for attempt in range(4):
   try:
    dec=zlib.decompressobj(-15)if info['compression']==8 else None;crc=count=0
    with urllib.request.urlopen(urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}'}),timeout=60)as r,pending.open('wb')as f:
     assert r.status==206 and r.headers['Content-Range'].startswith(f'bytes {start}-{end}/')
     while raw:=r.read(1024*1024):
      data=dec.decompress(raw)if dec else raw;f.write(data);count+=len(data);crc=zlib.crc32(data,crc)
     if dec:
      data=dec.flush();f.write(data);count+=len(data);crc=zlib.crc32(data,crc)
    assert count==info['bytes']and crc==info['crc'];os.replace(pending,target);return self.metadata(name,target)
   except (OSError,AssertionError):
    pending.unlink(missing_ok=True)
    if attempt==3:raise
    time.sleep(1)
 def metadata(self,name,target):
  h=hashlib.sha256()
  with target.open('rb')as f:
   while b:=f.read(1024*1024):h.update(b)
  return dict(entry=name,bytes=target.stat().st_size,sha256=h.hexdigest(),url=URL)
