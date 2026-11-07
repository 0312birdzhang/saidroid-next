"""Typed implementation of the original Libcore scratch-directory preparer.

No shell command is executed. Existing fixture roots are never replaced, and
cleanup follows only the inode created by this transaction. This module is
prepared for a future harness revision; it is not wired into active phone runs.
"""
from pathlib import Path
import errno,os,shutil,stat

_CTS_DATA=Path('/data')
_ROOT='/data/local/tmp/ctslibcore'
_CHILDREN=('java.io.tmpdir','user.home')
_MKDIR={'mkdir -p '+_ROOT+'/'+name for name in _CHILDREN}
_REMOVE='rm -rf '+_ROOT

def directory_spec(preparers):
    matches=[]
    for preparer in preparers:
        if preparer.get('class')!='com.android.tradefed.targetprep.RunCommandTargetPreparer':continue
        options=preparer.get('options',[])
        commands=[o['value']for o in options if o.get('name')=='run-command']
        teardown=[o['value']for o in options if o.get('name')=='teardown-command']
        if not any(_ROOT in value for value in commands+teardown):continue
        if len(commands)!=2 or set(commands)!=_MKDIR or teardown!=[_REMOVE]:
            raise ValueError('Unsupported or ambiguous original Libcore directory preparation')
        matches.append(dict(schema='cts-original-libcore-directories-v1',root=_ROOT,children=list(_CHILDREN),
                    original_commands=commands,original_teardown=teardown))
    if len(matches)>1:raise ValueError('Duplicate Libcore directory preparers')
    return matches[0]if matches else None

def _identity(path):
    value=os.lstat(path)
    if not stat.S_ISDIR(value.st_mode):raise RuntimeError('Preparer path is not a real directory: '+str(path))
    return dict(path=str(path),device=value.st_dev,inode=value.st_ino,uid=value.st_uid,gid=value.st_gid)

def _protected(path):
    identity=_identity(path);value=os.lstat(path)
    if identity['uid']!=0 or stat.S_IMODE(value.st_mode)&0o022:
        raise RuntimeError('Untrusted preparer parent: '+str(path))
    return identity

def _traversable(path,uid,gid):
    value=os.lstat(path)
    bit=stat.S_IXUSR if value.st_uid==uid else stat.S_IXGRP if value.st_gid==gid else stat.S_IXOTH
    if not value.st_mode&bit:raise PermissionError('Runtime user cannot traverse preparer parent: '+str(path))

def prepare_directories(spec,state,uid,gid):
    if os.geteuid()!=0:raise PermissionError('Temporary directory preparation requires its root preparer')
    if type(uid)is not int or type(gid)is not int or uid<=0 or gid<=0:
        raise ValueError('A real unprivileged fixture owner is required')
    expected=dict(schema='cts-original-libcore-directories-v1',root=_ROOT,children=list(_CHILDREN))
    if any(spec.get(key)!=value for key,value in expected.items()):raise ValueError('Unrecognized directory fixture')
    if len(spec.get('original_commands',[]))!=2 or set(spec.get('original_commands',[]))!=_MKDIR or spec.get('original_teardown')!=[_REMOVE]:
        raise ValueError('The original directory commands differ')
    if state:raise RuntimeError('Directory transaction state must be new')
    # Check every existing ancestor. The caller cannot redirect the fixed data
    # anchor through the instrumentation request or its writable app record.
    for parent in reversed([_CTS_DATA,*_CTS_DATA.parents]):_protected(parent);_traversable(parent,uid,gid)
    state.update(schema=expected['schema'],parents=[],root=None,cleaned=False)
    parent=_CTS_DATA
    for name in ['local','tmp']:
        parent=parent/name
        try:os.mkdir(parent,0o755)
        except FileExistsError:_protected(parent);_traversable(parent,uid,gid)
        else:
            state['parents'].append(_identity(parent));os.chmod(parent,0o755);_protected(parent)
    root=parent/'ctslibcore'
    # mkdir's O_EXCL-like directory creation also rejects dangling symlinks.
    os.mkdir(root,0o755);state['root']=_identity(root)
    for name in _CHILDREN:
        path=root/name;os.mkdir(path,0o700);os.chown(path,uid,gid)
    # Keep the containing directory root-owned until every privileged chown
    # below it is complete. Otherwise its new owner could replace a child
    # with a symlink between mkdir and chown.
    os.chown(root,uid,gid);state['root']=_identity(root)
    state['prepared_paths']=[str(root/name)for name in _CHILDREN]
    state['fixture_uid']=uid
    return state

def _unchanged(record):
    actual=_identity(record['path'])
    if any(actual[key]!=record[key]for key in ['device','inode','uid','gid']):
        raise RuntimeError('Temporary preparer directory identity changed: '+record['path'])
    return Path(record['path'])

def cleanup_directories(state):
    if not state:return
    if state.get('cleaned'):raise RuntimeError('Temporary directory transaction already cleaned')
    root=state.get('root')
    if root:
        path=_unchanged(root)
        # Linux's fd-based rmtree rejects a swapped top directory and does not
        # follow symlinks created by an application inside its scratch root.
        if not shutil.rmtree.avoids_symlink_attacks:
            raise RuntimeError('Descriptor-based scratch cleanup is unavailable')
        shutil.rmtree(path)
    for record in reversed(state.get('parents',[])):
        path=_unchanged(record)
        try:os.rmdir(path)
        except OSError as error:
            if error.errno in [errno.ENOTEMPTY,errno.EEXIST]:
                raise RuntimeError('New preparer parent acquired unrelated contents; retained: '+str(path))from error
            raise
    state['cleaned']=True
