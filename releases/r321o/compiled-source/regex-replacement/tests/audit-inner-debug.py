from pathlib import Path
import json,zipfile,hashlib,struct
base=Path('/media/psf/Home/WorkSpace/saidroid-next/build/evidence/cts-frame-repair-20261031');m=Path('/var/tmp/saidroid-regex-replacement248-module-v2');meta=json.loads((m/'manifest.json').read_text());before=next(Path(n)for n in meta['inputs']if n.endswith('/core-oj-classes.jar'));after=m/'core-oj-classes.jar';name='java/util/regex/Matcher$OffsetBasedMatchResult.class';sha=lambda d:hashlib.sha256(d).hexdigest()
with zipfile.ZipFile(before)as z:old=z.read(name)
with zipfile.ZipFile(after)as z:new=z.read(name)
assert old!=new;data=bytearray(new);u2=lambda i:struct.unpack_from('>H',data,i)[0];u4=lambda i:struct.unpack_from('>I',data,i)[0];assert data[:4]==b'\xca\xfe\xba\xbe';i=10;cp={};index=1
while index<u2(8):
 tag=data[i];i+=1
 if tag==1:
  length=u2(i);i+=2;cp[index]=bytes(data[i:i+length]).decode();i+=length
 elif tag in [3,4,9,10,11,12,17,18]:i+=4
 elif tag in [5,6]:i+=8;index+=1
 elif tag in [7,8,16,19,20]:i+=2
 elif tag==15:i+=3
 else:raise AssertionError(tag)
 index+=1
changes=[]
def attributes(pos,count):
 for _ in range(count):
  name=cp[u2(pos)];length=u4(pos+2);start=pos+6;end=start+length
  if name=='Code':
   j=start+8+u4(start+4);j+=2+8*u2(j);assert attributes(j+2,u2(j))==end
  elif name=='LineNumberTable':
   n=u2(start);assert length==2+4*n
   for x in range(n):
    offset=start+2+x*4+2;line=u2(offset);changes.append(dict(offset=offset,from_line=line,to_line=line-4));struct.pack_into('>H',data,offset,line-4)
  pos=end
 return pos
i+=6;i+=2+2*u2(i)
for _ in range(2):
 count=u2(i);i+=2
 for _ in range(count):i=attributes(i+8,u2(i+6))
i=attributes(i+2,u2(i));assert i==len(data)and changes and bytes(data)==old
r=dict(scope='Actual innerMatcher class differs only LineNumberTable entries uniformly+4 from longer canonicalhelper. Normalize precisely those u2linevalues and entireclassfilebyteidentical. Executablecode/constantpool/members/flags/allotherattributes unchanged; not claim innerclassbytes originallyidentical.',passed=True,module_manifest_sha256=sha((m/'manifest.json').read_bytes()),class_name=name,before_class_sha256=sha(old),after_class_sha256=sha(new),normalized_after_sha256=sha(bytes(data)),exact_entire_class_equal_after_line_only_normalization=True,line_entries=len(changes),line_changes=changes)
p=base/'regex-replacement248-inner-debug-v2-audit.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
