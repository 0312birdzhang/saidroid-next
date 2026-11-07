from pathlib import Path
import subprocess,struct,zipfile,os,hashlib,json
import sys
root=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]);assert str(out).startswith('/var/tmp/saidroid-next-');out.mkdir()
java=Path('/tmp/jdkfull/jdk-21.0.13+9');art=Path('/tmp/art-build/art-standalone/out/host/linux-x86')
source=root/'third_party/android-23-arm64/android-all-6.0.1_r3-robolectric-r1.jar'
cls=out/'classes';(cls/'android/text').mkdir(parents=True)
with zipfile.ZipFile(source)as z:data=z.read('android/text/StaticLayout.class')
before=b'(Ljava/nio/ByteBuffer;I)J';after=b'(Ljava/lang/String;)J'
needle=struct.pack('>H',len(before))+before
assert data.count(needle)==1
data=data.replace(needle,struct.pack('>H',len(after))+after)
(cls/'android/text/StaticLayout.class').write_bytes(data)
subprocess.run([str(java/'bin/javac'),'--release','8','-nowarn','-cp',str(cls)+':'+str(source),'-d',str(cls),str(root/'scripts/framework/text/Hyphenator.java')],check=True)
env=dict(os.environ,JAVA_HOME=str(java),PATH=str(java/'bin')+':'+os.environ['PATH'])
subprocess.run([str(art/'bin/dx'),'--dex','--force-jumbo','--output='+str(out/'patch.dex'),str(cls)],env=env,check=True)
original=Path(sys.argv[2])
with zipfile.ZipFile(original)as z:(out/'original.dex').write_bytes(z.read('classes.dex'))
tools='/var/tmp/saidroid-next-dex-tools-20261025-r1/root/usr/share/java/*'
(out/'tools').mkdir()
subprocess.run([str(java/'bin/javac'),'--release','8','-cp',tools,'-d',str(out/'tools'),str(root/'scripts/framework/ReplaceDexClasses.java')],check=True)
subprocess.run([str(java/'bin/java'),'-cp',str(out/'tools')+':'+tools,'ReplaceDexClasses',str(out/'original.dex'),str(out/'patch.dex'),str(out/'merged.dex'),'Landroid/text/StaticLayout;,Landroid/text/Hyphenator;'],check=True)
with zipfile.ZipFile(out/'framework3-hostdex.jar','w',zipfile.ZIP_DEFLATED)as z:z.writestr('classes.dex',(out/'merged.dex').read_bytes())
# Bundle the actual pattern data consumed by this native Minikin version.
import shutil
input_data=Path(sys.argv[3]);(out/'hyphen-data').mkdir()
files=[]
for item in sorted(input_data.iterdir()):
 if item.name.endswith(('.pat.txt','.lic.txt'))or item.name=='provenance.json':
  shutil.copyfile(item,out/'hyphen-data'/item.name)
  files.append(item.name)
assert len([n for n in files if n.endswith('.pat.txt')])==8
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(original_sha256=sha(original),new_sha256=sha(out/'framework3-hostdex.jar'),dictionaries={n:sha(out/'hyphen-data'/n)for n in files},aosp_source_sha256=sha(root/'scripts/framework/text/Hyphenator.aosp.java'))
(out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
