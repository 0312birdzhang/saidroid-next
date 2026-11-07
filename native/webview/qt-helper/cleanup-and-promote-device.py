"""Verify a retained development component, select it, clean only our test APK."""
from pathlib import Path
import hashlib,json,os,pwd,shutil,subprocess,sys
release=Path('/home/art/releases')/sys.argv[1]
assert release.parent==Path('/home/art/releases') and release.name.startswith('api29-')
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
assert Path('/home/art/test/.device-lock/owner').is_file()
assert release.is_dir() and not release.is_symlink()
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  exe=os.readlink(proc/'exe');cmd=(proc/'cmdline').read_bytes()
  assert not (exe.startswith('/home/art/releases/') and exe.endswith('/sdwebviewd'))
  assert not (b'api29-root/lib/runtime.jar' in cmd or cmd.startswith(b'saildroid-supervisor:'))
 except OSError:pass
manifest=json.loads((release/'install-manifest.json').read_text())
for name,item in manifest['files'].items():
 file=release/name
 assert file.is_file() and not file.is_symlink()
 assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256'],name
 assert file.stat().st_mode&0o777==item['mode'],name
for name,target in manifest['symlinks'].items():assert os.readlink(release/name)==target
print('COMPONENT_VERIFY=ready|files='+str(len(manifest['files'])),flush=True)
link=Path('/home/art/api29-root');old=os.readlink(link)
tmp=link.with_name('.api29-root-promote-'+str(os.getpid()));tmp.symlink_to(str(release));os.replace(tmp,link)
record={'previous':old,'current':str(release),'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'verified_files':len(manifest['files'])}
Path('/home/art/test/codex-r84-promotion.json').write_text(json.dumps(record,indent=2))
pkg='org.example.saildroid.webviewprobe';base=Path('/home/art/apps')/pkg
state=Path('/run/user/100000/saildroid')/(pkg+'.json')
if state.exists():assert json.loads(state.read_text()).get('state')=='exited'
if base.exists():
 assert not base.is_symlink()
 app=json.loads((base/'record.json').read_text());assert app['package']==pkg and app['data']==str(base/'data')
 shutil.rmtree(base)
 print('WEBVIEW_PROBE_CLEANUP=ready|private-apk-removed|desktop_entries_created=0',flush=True)
subprocess.run(['mcetool','--set-never-blank=disabled','--blank-screen'],check=True)
print('DEVELOPMENT_COMPONENT=selected|'+json.dumps(record),flush=True)
