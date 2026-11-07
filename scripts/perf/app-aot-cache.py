#!/usr/bin/env python3
"""Install or exchange complete, verified per-APK ART cache directories.

Run as the application owner with all SailDroid runtimes closed. The caller
owns the device lock. APKs, application data and runtime inputs are read-only.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,stat

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def require(condition,message):
    if not condition:raise RuntimeError(message)

def quiescent():
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            exe=os.readlink(proc/'exe')
            if exe.startswith(('/home/art/releases/','/opt/saildroid/')) and exe.endswith('/libexec/saildroid-host'):
                raw=(proc/'stat').read_text();state=raw[raw.rfind(') ')+2:].split()[0]
                require(state in ('Z','X'),'SailDroid runtime is still active: '+proc.name)
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue

def app_paths(package,app_home):
    require(re.fullmatch(r'[A-Za-z][\w]*(\.[A-Za-z_][\w]*)+',package),'Invalid package')
    base=app_home/package;require(base.is_dir() and not base.is_symlink(),'Application path is not a real directory')
    record=json.loads((base/'record.json').read_text());apk=Path(record['apk'])
    require(record['package']==package and apk.is_absolute() and apk.resolve()==apk and base in apk.parents,'APK escapes its application directory')
    require(apk.is_file() and apk.stat().st_uid==os.getuid(),'Run as the installed APK owner')
    oat=apk.parent/'oat';require(not oat.is_symlink(),'OAT path is a symlink');oat.mkdir(exist_ok=True)
    target=oat/'arm64';require(not target.is_symlink(),'Cache target is a symlink')
    return record,apk,oat,target

def checked_cache(source,record,apk,root):
    manifest_path=source/'saidroid-cache-manifest.json';manifest=json.loads(manifest_path.read_text())
    require(manifest['schema']=='saidroid-app-aot-cache-v2','Unsupported cache manifest')
    identity=manifest['identity'];key=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(key==manifest['cache_key'],'Cache identity key mismatch')
    guard=manifest['install_preconditions'];require(guard['package']==record['package'] and guard['apk']==str(apk),'Installed APK location mismatch')
    require(guard['signers']==record['signers'],'APK signer record mismatch')
    require(digest(apk)==guard['apk_sha256']==record['apkSha256']==identity['apk_sha256'],'Original APK hash mismatch')
    for name,sha in guard['runtime_inputs'].items():
        relative=Path(name);require(not relative.is_absolute() and '..' not in relative.parts,'Unsafe runtime input path')
        require(digest(root/relative)==sha,'Runtime input mismatch: '+name)
    require(set(manifest['files'])=={'base.odex','base.vdex'},'Cache must contain ODEX and VDEX')
    for name,item in manifest['files'].items():
        p=source/name;require(p.is_file() and not p.is_symlink(),'Cache input is not a regular file')
        require(p.stat().st_size==item['bytes'] and digest(p)==item['sha256'],'Cache payload mismatch: '+name)
    return manifest

def safe_label(value):
    require(re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',value),'Invalid cache transaction label');return value

def sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def install(source,package,root,run,app_home=Path('/home/art/apps'),adopt_source=False):
    safe_label(run);quiescent();record,apk,oat,target=app_paths(package,app_home)
    manifest=checked_cache(source,record,apk,root)
    pending=oat/('arm64.pending-'+run);backup=oat/('arm64.saved-'+run)
    require(not pending.exists() and not backup.exists(),'Transaction path already exists')
    if adopt_source:
        # A verified upload on the same filesystem can become the pending
        # directory itself. Large QQ caches otherwise need a second full copy.
        require(source.is_absolute() and source.resolve()==source and source.is_dir() and not source.is_symlink(),'Invalid adopt source')
        require(source.stat().st_uid==os.getuid() and source.stat().st_mode&0o022==0,'Adopt source ownership or mode differs')
        require(source.stat().st_dev==oat.stat().st_dev,'Adopt source is on another filesystem')
        require(source!=oat and source not in oat.parents and oat not in source.parents,'Adopt source overlaps application cache')
        require({p.name for p in source.iterdir()}==set(manifest['files'])|{'saidroid-cache-manifest.json'},'Unexpected adopt source entry')
        for p in source.iterdir():
            require(p.is_file() and not p.is_symlink() and p.stat().st_nlink==1 and p.stat().st_uid==os.getuid() and p.stat().st_mode&0o022==0,'Unsafe adopt source file')
    required=128*1024*1024+(0 if adopt_source else sum(v['bytes']for v in manifest['files'].values()))
    require(shutil.disk_usage(oat).free>required,'Insufficient cache space')
    if adopt_source:os.rename(source,pending)
    else:pending.mkdir(mode=0o700)
    try:
        for name,item in manifest['files'].items():
            if adopt_source:
                with (pending/name).open('rb')as stream:os.fsync(stream.fileno())
            else:
                with (source/name).open('rb')as src,(pending/name).open('xb')as dst:
                    shutil.copyfileobj(src,dst,1024*1024);dst.flush();os.fsync(dst.fileno())
            (pending/name).chmod(0o644);require(digest(pending/name)==item['sha256'],'Copied cache hash mismatch')
        p=pending/'saidroid-cache-manifest.json';p.write_text(json.dumps(manifest,indent=2)+'\n');p.chmod(0o644)
        with p.open('rb')as stream:os.fsync(stream.fileno())
        pending.chmod(0o755);sync_directory(pending)
        quiescent();require(digest(apk)==record['apkSha256'],'APK changed during transfer')
        existed=target.exists()
        if existed:require(target.is_dir() and not target.is_symlink(),'Invalid old cache');os.rename(target,backup)
        else:backup.mkdir(mode=0o755)
        try:
            os.rename(pending,target);sync_directory(oat)
            if adopt_source:sync_directory(source.parent)
        except BaseException:
            if existed:os.rename(backup,target)
            else:backup.rmdir()
            raise
        return dict(passed=True,package=package,cache_key=manifest['cache_key'],target=str(target),backup=str(backup),previous_cache_existed=existed,apk_sha256=record['apkSha256'],source_adopted=adopt_source)
    except BaseException:
        # Keep incomplete bytes for diagnosis; never delete a previous cache.
        raise

def switch(package,to,save_as,app_home=Path('/home/art/apps')):
    safe_label(to);safe_label(save_as);require(to!=save_as,'Identical source and destination labels');quiescent()
    record,apk,oat,target=app_paths(package,app_home);desired=oat/('arm64.saved-'+to);saved=oat/('arm64.saved-'+save_as)
    require(desired.is_dir() and not desired.is_symlink() and not saved.exists(),'Invalid saved cache transaction')
    require(target.is_dir() and not target.is_symlink(),'No current cache directory');os.rename(target,saved)
    try:os.rename(desired,target);sync_directory(oat)
    except BaseException:os.rename(saved,target);raise
    return dict(passed=True,package=package,selected=to,saved_as=save_as,apk_sha256=digest(apk))

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    install_parser=sub.add_parser('install');install_parser.add_argument('--source',type=Path,required=True);install_parser.add_argument('--root',type=Path,required=True);install_parser.add_argument('--run',required=True)
    install_parser.add_argument('--adopt-source',action='store_true',help='Move an owned, verified upload on the same filesystem without a second payload copy')
    switch_parser=sub.add_parser('switch');switch_parser.add_argument('--to',required=True);switch_parser.add_argument('--save-as',required=True)
    for q in [install_parser,switch_parser]:q.add_argument('--package',required=True)
    a=p.parse_args();result=install(a.source,a.package,a.root,a.run,adopt_source=a.adopt_source)if a.action=='install'else switch(a.package,a.to,a.save_as);print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
