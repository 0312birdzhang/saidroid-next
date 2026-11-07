#!/usr/bin/env python3
"""Read APK binary AndroidManifest.xml metadata without changing APK bytes."""
from pathlib import Path
import struct,zipfile,json,sys

def parse(apk):
 with zipfile.ZipFile(apk)as archive:b=archive.read('AndroidManifest.xml')
 def u16(o):return struct.unpack_from('<H',b,o)[0]
 def u32(o):return struct.unpack_from('<I',b,o)[0]
 strings=[];root=None;stack=[];offset=u16(2)
 while offset<len(b):
  kind,header,size=struct.unpack_from('<HHI',b,offset)
  if size<8 or offset+size>len(b):raise ValueError('Invalid binary XML chunk bounds')
  if kind==1:
   count=u32(offset+8);flags=u32(offset+16);start=offset+u32(offset+20);strings=[]
   for i in range(count):
    pos=start+u32(offset+header+4*i)
    def length(p,utf8):
     if utf8:
      n=b[p];return(((n&127)<<8)|b[p+1],p+2)if n&128 else(n,p+1)
     n=u16(p);return(((n&32767)<<16)|u16(p+2),p+4)if n&32768 else(n,p+2)
    _,pos=length(pos,bool(flags&256));
    if flags&256:
     n,pos=length(pos,True);value=b[pos:pos+n].decode('utf-8')
    else:n=_;value=b[pos:pos+2*n].decode('utf-16le')
    strings.append(value)
  elif kind==0x102:
   name=strings[u32(offset+20)];start=offset+16+u16(offset+24);width=u16(offset+26);count=u16(offset+28);attrs={}
   for i in range(count):
    pos=start+i*width;key=strings[u32(pos+4)];raw=u32(pos+8);typ=b[pos+15];value=u32(pos+16)
    attrs[key]=strings[raw]if raw!=0xffffffff else strings[value]if typ==3 else bool(value)if typ==18 else value
   node={'tag':name,'attributes':attrs,'children':[]}
   if stack:stack[-1]['children'].append(node)
   else:root=node
   stack.append(node)
  elif kind==0x103:
   if not stack:raise ValueError('Unbalanced manifest')
   stack.pop()
  offset+=size
 if not root or stack:raise ValueError('Invalid manifest root')
 attrs=root['attributes'];package=attrs['package'];instruments=[];app=next((n for n in root['children']if n['tag']=='application'),None)
 def expand(name):return package+name if name.startswith('.')else package+'.'+name if'.'not in name else name
 for n in root['children']:
  if n['tag']=='instrumentation':
   row=dict(n['attributes']);row['name']=expand(row['name']);instruments.append(row)
 return dict(package=package,version_code=attrs.get('versionCode'),instrumentation=instruments,application=app['attributes']if app else{},manifest=root)
if __name__=='__main__':print(json.dumps(parse(Path(sys.argv[1])),indent=2))
