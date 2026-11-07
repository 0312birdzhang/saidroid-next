#!/usr/bin/env python3
"""Build the unchanged Android10 Toybox touch command for private app PATH use."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,tarfile,urllib.request,shutil
p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--archive',type=Path);a=p.parse_args()
source=json.loads(Path(__file__).with_name('toybox-source.json').read_text());assert not a.output.exists();a.output.mkdir(parents=True)
data=a.archive.read_bytes()if a.archive else urllib.request.urlopen(source['url'],timeout=60).read()
assert len(data)==source['bytes'] and hashlib.sha256(data).hexdigest()==source['sha256']
archive=a.output/'source.tar.gz';archive.write_bytes(data);tree=a.output/'source';tree.mkdir()
with tarfile.open(archive)as t:
 for m in t.getmembers():
  assert not Path(m.name).is_absolute() and '..'not in Path(m.name).parts
  assert m.isfile()or m.isdir()or(m.issym()and m.name in ['NOTICE','www/index.html']and m.linkname in ['LICENSE','news.html']),'Unexpected archive special entry'
 t.extractall(tree)
env=dict(os.environ,CC='gcc',HOSTCC='gcc',CFLAGS='-O2',LC_ALL='C')
with(a.output/'build.log').open('x')as log:
 subprocess.run(['make','allnoconfig'],cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 config=tree/'.config';text=config.read_text()
 for name in ['TOUCH','TOYBOX','TOYBOX_HELP']:
  old='# CONFIG_'+name+' is not set';assert old in text or 'CONFIG_'+name+'=y' in text;text=text.replace(old,'CONFIG_'+name+'=y')
 config.write_text(text)
 subprocess.run(['make','-j2'],cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
binary=a.output/'toybox';shutil.copyfile(tree/'toybox',binary);binary.chmod(0o755)
assert 'AArch64'in subprocess.check_output(['readelf','-h',str(binary)],text=True)
listing=subprocess.check_output([str(binary)],text=True).split();assert listing==['touch'],listing
notice=a.output/'NOTICE';notice.write_bytes((tree/'LICENSE').read_bytes())
record=dict(schema='saildroid-private-commands-v1',upstream=source,commands=['touch'],source_changes=[],binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),notice_sha256=hashlib.sha256(notice.read_bytes()).hexdigest(),config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),architecture='AArch64',scope='Real unchanged Android10 Toybox command; application UID, no capabilities or system install')
(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('ANDROID_COMMANDS=compiled|commands=touch|source=android-10.0.0_r16|unchanged=true')
