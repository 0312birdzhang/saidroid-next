#!/usr/bin/env python3
"""Root the original API23 font loader in the private runtime and supply its fonts.

Only two original class UTF8 path constants change; class structure, bytecode,
callbacks and native signatures remain intact. Original class files are retained.
"""
from pathlib import Path
import hashlib
import json
import os
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

output = Path(sys.argv[1])
original_jar = Path(sys.argv[2])
host_cjk = Path(sys.argv[3])
if not str(output).startswith('/var/tmp/saidroid-next-'):
    raise SystemExit('Fresh isolated VM output directory required')
output.mkdir(mode=0o700)
image = Path('/tmp/and23/arm64-v8a/system.img')
art = Path('/tmp/art-build/art-standalone/out/host/linux-x86')
java = Path('/tmp/jdkfull/jdk-21.0.13+9')
root = Path(__file__).resolve().parents[1]
framework_source = root/'third_party/android-23-arm64/android-all-6.0.1_r3-robolectric-r1.jar'
sha = lambda data: hashlib.sha256(data).hexdigest()
if sha(framework_source.read_bytes()) != 'a2d84271c5f033b1d082741a02f37a2d043120c0c09e5854e97ece9c3bb11d31':
    raise SystemExit('Font classes must come from the recorded API23 framework source')

def patch_utf8(data, before, after):
    assert data[:4] == b'\xca\xfe\xba\xbe'
    count = struct.unpack_from('>H', data, 8)[0]
    cursor, index, changed = 10, 1, 0
    result = bytearray(data[:10])
    while index < count:
        start = cursor
        tag = data[cursor]
        cursor += 1
        if tag == 1:
            length = struct.unpack_from('>H', data, cursor)[0]
            cursor += 2
            value = data[cursor:cursor + length]
            cursor += length
            if value == before:
                result.extend(b'\x01' + struct.pack('>H', len(after)) + after)
                changed += 1
            else:
                result.extend(data[start:cursor])
        else:
            widths = {3:4,4:4,5:8,6:8,7:2,8:2,9:4,10:4,11:4,12:4,15:3,16:2,17:4,18:4,19:2,20:2}
            cursor += widths[tag]
            result.extend(data[start:cursor])
            if tag in (5, 6):index += 1
        index += 1
    assert changed == 1, (before, changed)
    result.extend(data[cursor:])  # All fields/methods/bytecode/attributes are unchanged.
    assert bytes(result).endswith(data[cursor:])
    return bytes(result)

def definitions(data):
    u=lambda offset:struct.unpack_from('<I',data,offset)[0]
    strings,types,count,table=u(60),u(68),u(96),u(100)
    result=set()
    for index in range(count):
        string=u(types+4*u(table+32*index));offset=u(strings+4*string)
        while data[offset]&128:offset+=1
        offset+=1;result.add(data[offset:data.index(0,offset)].decode())
    assert len(result)==count
    return result

fontdir=output/'fonts';fontdir.mkdir()
config=output/'fonts.xml'
subprocess.run(['debugfs','-R','dump /etc/fonts.xml '+str(config),str(image)],check=True,capture_output=True)
xml=ET.fromstring(config.read_bytes())
font_names=sorted({element.text.strip() for element in xml.iter('font')})
assert len(font_names)>20
listing=subprocess.run(['debugfs','-R','ls -p /fonts',str(image)],check=True,capture_output=True,text=True).stdout
available={line.split('/')[5] for line in listing.splitlines() if line.startswith('/') and len(line.split('/'))>6}
missing=set(font_names)-available
assert missing=={'DroidSansFallback.ttf','MTLmr3m.ttf','NanumGothic.ttf'}
original_config=config.read_bytes()
adjusted=original_config
for name in sorted(missing):
    before=b'>'+name.encode()+b'</font>'
    assert adjusted.count(before)==1
    adjusted=adjusted.replace(before,b'>wqy-zenhei.ttc</font>')
config.write_bytes(adjusted)
host_font=host_cjk.read_bytes()
assert len(host_font)>1000000 and host_font[:4]==b'ttcf'
(fontdir/'wqy-zenhei.ttc').write_bytes(host_font)
(fontdir/'wqy-zenhei.ttc').chmod(0o644)
files={}
files['wqy-zenhei.ttc']=dict(bytes=len(host_font),sha256=sha(host_font))
for name in sorted(set(font_names)-missing):
    assert name==Path(name).name and name not in ('.','..')
    target=fontdir/name
    subprocess.run(['debugfs','-R','dump /fonts/'+name+' '+str(target),str(image)],check=True,capture_output=True)
    raw=target.read_bytes()
    assert len(raw)>1000 and raw[:4] in (b'\x00\x01\x00\x00',b'OTTO',b'ttcf'),name
    target.chmod(0o644)
    files[name]=dict(bytes=len(raw),sha256=sha(raw))
config.chmod(0o644)
patches={
 'android/graphics/Typeface.class':(b'/system/etc/',b'/home/art/etc/'),
 'android/graphics/FontListParser.class':(b'/system/fonts/',b'/home/art/fonts/'),
}
patched=output/'patched-classes';original=output/'original-classes'
class_records={}
for name,(before,after) in patches.items():
    with zipfile.ZipFile(framework_source) as source:
        data=source.read(name)
    changed=patch_utf8(data,before,after)
    for base,raw in [(original,data),(patched,changed)]:
        path=base/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    class_records[name]=dict(before_sha256=sha(data),after_sha256=sha(changed),
                             before_path=before.decode(),after_path=after.decode())
env=dict(os.environ,JAVA_HOME=str(java),PATH=str(java/'bin')+':'+os.environ['PATH'])
subprocess.run([str(art/'bin/dx'),'--dex','--force-jumbo','--output='+str(output/'font-paths.dex'),str(patched)],env=env,check=True)
with zipfile.ZipFile(original_jar) as archive:original_dex=archive.read('classes.dex')
(output/'original.dex').write_bytes(original_dex)
tools = Path(os.environ.get('DEX_TOOL_JARS', '/var/tmp/saidroid-next-dex-tools-20261025-r1/root/usr/share/java'))
toolclasses = output/'dex-tool-classes';toolclasses.mkdir()
classpath = str(tools/'*')
subprocess.run([str(java/'bin/javac'),'--release','8','-nowarn','-cp',classpath,'-d',str(toolclasses),
                str(root/'scripts/framework/ReplaceDexClasses.java')],check=True)
subprocess.run([str(java/'bin/java'),'-cp',str(toolclasses)+':'+classpath,'ReplaceDexClasses',
                str(output/'original.dex'),str(output/'font-paths.dex'),str(output/'merged.dex')],check=True)
merged=(output/'merged.dex').read_bytes()
assert definitions(merged)==definitions(original_dex)
assert definitions((output/'font-paths.dex').read_bytes())=={'Landroid/graphics/Typeface;','Landroid/graphics/FontListParser;'}
target=output/'framework2-hostdex.jar'
with zipfile.ZipFile(target,'x') as archive:
    info=zipfile.ZipInfo('classes.dex',(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
    archive.writestr(info,merged)
record=dict(schema='saidroid-private-font-runtime-v1',image=str(image),image_sha256=sha(image.read_bytes()),
             framework_source_sha256=sha(framework_source.read_bytes()),
             original_jar_sha256=sha(original_jar.read_bytes()),new_jar_sha256=sha(target.read_bytes()),
             classes=class_records,total_classes=len(definitions(merged)),
             original_config_sha256=sha(original_config),config_sha256=sha(config.read_bytes()),
             fallback_replacements={name:'wqy-zenhei.ttc' for name in sorted(missing)},
             fallback_source='/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc',fonts=files)
(output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({key:value for key,value in record.items() if key!='fonts'},indent=2))
print('font_files='+str(len(files)))
