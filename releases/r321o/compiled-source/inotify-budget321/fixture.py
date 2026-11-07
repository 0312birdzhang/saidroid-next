import ctypes,errno,json,os,pathlib,select,statistics,struct,sys,tempfile,threading,time
g=ctypes.CDLL(sys.argv[1],use_errno=True);lib=ctypes.CDLL(None,use_errno=True)
for f in [g.inotify_add_watch,g.bionic_inotify_add_watch,lib.inotify_add_watch]:f.argtypes=(ctypes.c_int,ctypes.c_char_p,ctypes.c_uint32)
g.sd_guard_fixture_configure_local.argtypes=(ctypes.c_char_p,ctypes.c_uint,ctypes.c_uint)
g.syscall.restype=g.bionic_syscall.restype=ctypes.c_long
g.syscall.argtypes=g.bionic_syscall.argtypes=(ctypes.c_long,)*7
lib.strdup.argtypes=(ctypes.c_char_p,);lib.strdup.restype=ctypes.c_void_p
CREATE,DELETE,ATTRIB,ONESHOT,MASK_ADD,MASK_CREATE,DONT_FOLLOW,ONLYDIR,IGNORED=0x100,0x200,4,0x80000000,0x20000000,0x10000000,0x2000000,0x1000000,0x8000
def config(lock,cap=3,instances=16):assert g.sd_guard_fixture_configure_local(os.fsencode(lock),cap,instances)==0
def init():
    fd=g.inotify_init1(os.O_NONBLOCK|os.O_CLOEXEC);assert fd>=0,('init',ctypes.get_errno());return fd
def add(fd,path,mask=CREATE,android=False):
    ctypes.set_errno(0);wd=(g.bionic_inotify_add_watch if android else g.inotify_add_watch)(fd,os.fsencode(path),mask);return wd,ctypes.get_errno()
def rows(fd):return [s for s in pathlib.Path('/proc/self/fdinfo/'+str(fd)).read_text().splitlines()if s.startswith('inotify ')]
def drain(fd):
    if not select.select([fd],[],[],0)[0]:return []
    raw=os.read(fd,65536);out=[];offset=0
    while offset<len(raw):
        wd,mask,cookie,n=struct.unpack_from('iIII',raw,offset);out.append(dict(wd=wd,mask=mask,cookie=cookie));offset+=16+n
    return out
def stats():
    out=(ctypes.c_ulong*4)();g.sd_guard_fixture_stats(out);return list(out)
proof=[]
with tempfile.TemporaryDirectory(prefix='saidroid-process-guard-')as tmp:
    root=pathlib.Path(tmp);lock=root/'lock';lock.mkdir(mode=0o700);config(lock)
    paths=[root/str(i)for i in range(530)]
    for path in paths:path.mkdir()
    fds=[init(),init()];wds=[add(fds[0],p)[0]for p in paths[:2]];wds.append(add(fds[1],paths[2])[0]);assert min(wds)>=0
    before=stats();rejected=add(fds[1],paths[3]);after=stats()
    assert rejected==(-1,errno.ENOSPC)and sum(len(rows(fd))for fd in fds)==3 and drain(fds[1])==[]
    assert after[1]==before[1],'local cap must avoid UID rescan'
    for mask in (DELETE,CREATE|MASK_ADD,CREATE|MASK_CREATE):assert add(fds[0],paths[0],mask)==(-1,errno.ENOSPC)
    assert g.inotify_rm_watch(fds[1],wds[2])==0 and len(rows(fds[1]))==0
    assert add(fds[0],paths[0],DELETE)[0]==wds[0]and add(fds[0],paths[0],CREATE|MASK_ADD)[0]==wds[0]
    ctypes.set_errno(0);native_mask_create=lib.inotify_add_watch(fds[0],os.fsencode(paths[0]),CREATE|MASK_CREATE);native_mask_errno=ctypes.get_errno()
    assert add(fds[0],paths[0],CREATE|MASK_CREATE)==(native_mask_create,native_mask_errno)
    wds[2]=add(fds[1],paths[2])[0];assert wds[2]>=0;drain(fds[1])
    proof.append(dict(case='cross-instance-process-cap-before-allocation',passed=True,local_cap=3,uid_rescans_on_local_rejection=after[1]-before[1],sum_rows=3,existing_update_at_cap="ENOSPC",existing_update_after_capacity_recovery="same-watch-descriptor"))
    dup=os.dup(fds[0]);os.close(fds[0]);fds[0]=dup
    assert add(dup,paths[0])==(-1,errno.ENOSPC)
    assert g.inotify_rm_watch(fds[1],wds[2])==0
    assert add(dup,paths[0])[0]==wds[0]
    assert add(fds[1],paths[3],CREATE|ONESHOT)[0]>=0
    (paths[3]/'event').write_text('x');assert len(rows(fds[1]))==0
    assert add(fds[1],paths[4])[0]>=0
    assert sum(bool(e['mask']&IGNORED)for e in drain(fds[1]))==2
    for fd in fds:os.close(fd)
    proof.append(dict(case='dup-close-rm-oneshot-reconciliation',passed=True))
    # Deterministically pause an existing-watch update while the process and
    # allocation locks are held; a normal/bionic/syscall rm must wait.
    for removal_kind in ['normal','bionic','syscall']:
        fd=init();wds=[add(fd,path)[0]for path in paths[:2]]
        notify_read,notify_write=os.pipe();resume_read,resume_write=os.pipe()
        g.sd_guard_fixture_pause_once(notify_write,resume_read);update_result=[];remove_result=[];entered=threading.Event()
        update=threading.Thread(target=lambda:update_result.append(add(fd,paths[0],DELETE)))
        def remove():
            entered.set()
            if removal_kind=='syscall':remove_result.append(g.syscall(28,fd,wds[0],0,0,0,0))
            else:remove_result.append((g.bionic_inotify_rm_watch if removal_kind=='bionic'else g.inotify_rm_watch)(fd,wds[0]))
        update.start();assert select.select([notify_read],[],[],3)[0];os.read(notify_read,1)
        remover=threading.Thread(target=remove);remover.start();assert entered.wait(1)
        time.sleep(.03);assert remove_result==[]and len(rows(fd))==2
        os.write(resume_write,b'x');update.join(timeout=3);remover.join(timeout=3)
        assert not update.is_alive()and not remover.is_alive()and update_result[0][0]==wds[0]and remove_result==[0]and len(rows(fd))==1
        for end in [notify_read,notify_write,resume_read,resume_write]:os.close(end)
        os.close(fd)
    proof.append(dict(case='rm-serialized-against-paused-update-below-cap',passed=True,paths=['normal','bionic','syscall'],during_rows=2,after_rows=1))
    # A child mutates an inherited instance, closes/exits, and the parent must
    # retain the added watch. A stale per-process ledger would lose this charge.
    fd=init();assert add(fd,paths[0])[0]>=0 and add(fd,paths[1])[0]>=0
    child=os.fork()
    if child==0:
        third=add(fd,paths[2]);os.close(fd);os._exit(0 if third[0]>=0 else 4)
    assert os.waitpid(child,0)[1]==0 and len(rows(fd))==3
    assert add(fd,paths[3])==(-1,errno.ENOSPC)
    assert add(fd,paths[0],ATTRIB)==(-1,errno.ENOSPC);os.close(fd)
    proof.append(dict(case='fork-child-exit-shared-instance-retains-capacity',passed=True,parent_live_rows=3,ledger_used=False))
    # Rename the final symlink component while a request holds guard locks.
    # Below the cap the kernel resolves the original path and allocates at most
    # one watch; at the cap even an earlier existing-path match is rejected.
    config(lock,cap=2);fd=init();old_wd=add(fd,paths[0],ATTRIB)[0]
    race_alias=root/'race-alias';race_alias.symlink_to(paths[0],target_is_directory=True)
    def paused_rename(destination):
        notify_read,notify_write=os.pipe();resume_read,resume_write=os.pipe()
        g.sd_guard_fixture_pause_once(notify_write,resume_read);out=[]
        worker=threading.Thread(target=lambda:out.append(add(fd,race_alias,ATTRIB)))
        worker.start();assert select.select([notify_read],[],[],3)[0];os.read(notify_read,1)
        replacement=root/'race-replacement';replacement.symlink_to(destination,target_is_directory=True);os.replace(replacement,race_alias)
        os.write(resume_write,b'x');worker.join(timeout=3);assert not worker.is_alive()
        for end in (notify_read,notify_write,resume_read,resume_write):os.close(end)
        return out[0]
    new_wd=paused_rename(paths[1])[0];assert new_wd>=0 and new_wd!=old_wd and len(rows(fd))==2
    race_alias.unlink();race_alias.symlink_to(paths[0],target_is_directory=True)
    assert paused_rename(paths[2])==(-1,errno.ENOSPC)and len(rows(fd))==2
    assert {int(line.split()[2].split(':')[1],16)for line in rows(fd)}=={paths[0].stat().st_ino,paths[1].stat().st_ino}
    os.close(fd);config(lock)
    proof.append(dict(case='renamed-target-at-cap-cannot-bypass-policy',passed=True,below_cap_resolves_replacement=True,at_cap_existing_path_request='ENOSPC',rows_never_exceed=2))
    # Exercise a fork while another thread repeatedly enters the guard. The
    # atfork mutex must not leave a shared flock OFD trapped in the child.
    fd=init();assert add(fd,paths[0])[0]>=0
    failures=[]
    def churn():
        for _ in range(20):
            if add(fd,paths[0],CREATE|MASK_ADD)[0]<0:failures.append('update')
    worker=threading.Thread(target=churn);worker.start();child=os.fork()
    if child==0:os._exit(0 if add(fd,paths[0],CREATE|MASK_ADD)[0]>=0 else 5)
    assert os.waitpid(child,0)[1]==0;worker.join(timeout=5);assert not worker.is_alive()and not failures
    os.close(fd);proof.append(dict(case='fork-during-guard-does-not-inherit-active-lock',passed=True))
    # Instance budget counts zero-watch descriptors; failed init creates no fd.
    config(lock,instances=4);fds=[init()for _ in range(4)]
    ctypes.set_errno(0);assert g.inotify_init1(os.O_CLOEXEC)==-1 and ctypes.get_errno()==errno.EMFILE
    for fd in fds:assert rows(fd)==[];os.close(fd)
    config(lock);proof.append(dict(case='local-instance-cap-counts-zero-watch-fds',passed=True,admitted=4))
    # Native error and policy precedence; ordinary valid lookup never bypasses access.
    fd=init();unreadable=root/'unreadable';unreadable.write_text('x');unreadable.chmod(0)
    assert add(fd,unreadable,ATTRIB)==(-1,errno.EACCES)
    assert add(fd,root/'missing')==(-1,errno.ENOENT)
    assert add(-1,paths[0])==(-1,errno.EBADF)
    regular=os.open(paths[0],os.O_RDONLY|os.O_DIRECTORY)
    assert add(regular,paths[0])==(-1,errno.EINVAL);os.close(regular)
    alias=root/'alias';alias.symlink_to(paths[0],target_is_directory=True)
    a=add(fd,alias,ATTRIB|DONT_FOLLOW)[0];b=add(fd,alias,ATTRIB)[0];assert a>=0 and b>=0 and a!=b
    assert add(fd,alias,ATTRIB|DONT_FOLLOW|ONLYDIR)==(-1,errno.ENOTDIR)
    assert add(fd,paths[1])[0]>=0
    assert add(fd,unreadable,ATTRIB)==(-1,errno.ENOSPC)
    os.close(fd);proof.append(dict(case='symlink-permissions-errors',passed=True,policy_precedence='ENOSPC at artificial cap may precede EACCES; no successful permission bypass'))
    # Android path callback is deliberately tri-state; normal host path is untouched.
    mapped=root/'mapped';mapped.mkdir();decoy=root/'decoy';decoy.mkdir()
    MAPPER=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_char_p,ctypes.POINTER(ctypes.c_void_p),use_errno=True)
    def translate(path,out):
        if path==b'/logical/private-watch':out[0]=lib.strdup(os.fsencode(mapped));return 1
        if path==b'/logical/allocation-failure':ctypes.set_errno(errno.ENOMEM);return -1
        return 0
    callback=MAPPER(translate);g.saildroid_inotify_set_path_mapper.argtypes=(MAPPER,);g.saildroid_inotify_set_path_mapper(callback)
    fd=init();assert add(fd,'/logical/private-watch',android=True)[0]>=0
    assert add(fd,'/logical/private-watch')==(-1,errno.ENOENT)
    assert add(fd,'/logical/allocation-failure',android=True)==(-1,errno.ENOMEM)
    assert add(fd,'/logical/private-watch-extra',android=True)==(-1,errno.ENOENT)
    (decoy/'event').write_text('x');assert drain(fd)==[]
    (mapped/'event').write_text('x');assert any(e['mask']&CREATE for e in drain(fd));os.close(fd)
    proof.append(dict(case='shared-tristate-path-mapping',passed=True,host_decoy_events=0))
    # Test every forwarded argument with actual mmap + offset, not just getpid.
    assert g.syscall(172,0,0,0,0,0,0)==os.getpid()
    ctypes.set_errno(0);assert g.syscall(999999,0,0,0,0,0,0)==-1 and ctypes.get_errno()==errno.ENOSYS
    data=root/'mmap-data';data.write_bytes(b'A'*4096+b'B'*4096);datafd=os.open(data,os.O_RDONLY)
    address=g.syscall(222,0,4096,1,2,datafd,4096);assert address not in [-1,0]and ctypes.string_at(address,8)==b'B'*8
    assert g.syscall(215,address,4096,0,0,0,0)==0;os.close(datafd)
    fd=g.syscall(26,os.O_NONBLOCK|os.O_CLOEXEC,0,0,0,0,0);assert fd>=0
    encoded=ctypes.create_string_buffer(b'/logical/private-watch');pointer=ctypes.addressof(encoded)
    wd=g.bionic_syscall(27,fd,pointer,CREATE,0,0,0);assert wd>=0
    assert g.syscall(28,fd,wd,0,0,0,0)==0
    for path in paths[:3]:
        encoded=ctypes.create_string_buffer(os.fsencode(path));assert g.syscall(27,fd,ctypes.addressof(encoded),CREATE,0,0,0)>=0
    encoded=ctypes.create_string_buffer(os.fsencode(paths[3]));ctypes.set_errno(0)
    syscall_result=g.syscall(27,fd,ctypes.addressof(encoded),CREATE,0,0,0);syscall_errno=ctypes.get_errno()
    assert syscall_result==-1 and syscall_errno==errno.ENOSPC,(syscall_result,syscall_errno,rows(fd),stats())
    os.close(fd);proof.append(dict(case='aarch64-syscall-six-arguments-and-inotify-routing',passed=True,real_mmap_offset=4096))
    # Five unrelated fixture processes race for ten policy slots. No app names.
    config(lock,cap=2)
    readers=[];releases=[];children=[]
    for number in range(5):
        read,write=os.pipe();exit_read,exit_write=os.pipe();child=os.fork()
        if child==0:
            os.close(read);os.close(exit_write);fd=init();results=[]
            for path in paths[number*3:number*3+3]:results.append(add(fd,path))
            os.write(write,json.dumps(dict(pid=os.getpid(),results=results,rows=len(rows(fd)))).encode());os.close(write);os.read(exit_read,1);os.close(fd);os._exit(0)
        os.close(write);os.close(exit_read);readers.append(read);releases.append(exit_write);children.append(child)
    records=[]
    try:
        for read in readers:
            assert select.select([read],[],[],5)[0];records.append(json.loads(os.read(read,4096)))
        assert sum(r['rows']for r in records)==10
        assert sum(wd>=0 for r in records for wd,err in r['results'])==10
        assert sum((wd,err)==(-1,errno.ENOSPC)for r in records for wd,err in r['results'])==5
        # Unguarded host remains able to allocate within the reserved example budget.
        host=lib.inotify_init1(os.O_NONBLOCK|os.O_CLOEXEC);assert host>=0
        for path in paths[20:24]:assert lib.inotify_add_watch(host,os.fsencode(path),CREATE)>=0
        assert len(rows(host))==4;os.close(host)
    finally:
        for write in releases:os.write(write,b'x');os.close(write)
        for read in readers:os.close(read)
        for child in children:assert os.waitpid(child,0)[1]==0
    proof.append(dict(case='five-process-independent-local-caps',passed=True,cap_each=2,global_uid_quota_claimed=False,guarded_watches=10,unguarded_host_watches=4,records=records))
    # Initialize the peer while it can inspect its own fdinfo. Dropping
    # dumpability is solely to deny the parent's access to that peer; it must
    # not silently turn this into a test of the child's self-census support.
    config(lock);fd=init();wd=add(fd,paths[0])[0];read,write=os.pipe();exit_read,exit_write=os.pipe();child=os.fork()
    if child==0:
        os.close(read);os.close(exit_write);own=-1;child_code=1
        try:
            own=init();assert add(own,paths[10])[0]>=0
            assert lib.prctl(4,0,0,0,0)==0 and lib.prctl(3,0,0,0,0)==0
            os.write(write,json.dumps(dict(ready=True,pid=os.getpid(),own_fd=own,dumpable=0)).encode());os.close(write);write=-1
            assert os.read(exit_read,1)==b'x';child_code=0
        except BaseException as error:
            if write>=0:
                try:os.write(write,json.dumps(dict(ready=False,error=repr(error))).encode())
                except OSError:pass
        finally:
            if own>=0:os.close(own)
            if write>=0:os.close(write)
            os.close(exit_read)
            # Never unwind the parent's inherited TemporaryDirectory context.
            os._exit(child_code)
    os.close(write);os.close(exit_read);peer_status=None;peer_access_errno=None
    try:
        assert select.select([read],[],[],3)[0];payload=os.read(read,4096)
        assert payload,'peer exited without readiness evidence';peer_status=json.loads(payload);assert peer_status.get('ready'),peer_status
        try:list(pathlib.Path('/proc/'+str(child)+'/fdinfo').iterdir())
        except OSError as error:peer_access_errno=error.errno
        assert peer_access_errno in (errno.EACCES,errno.EPERM),peer_access_errno
        before=stats();assert add(fd,paths[1])[0]>=0
        assert add(fd,paths[0],DELETE)[0]==wd
        after=stats();assert after[1]==before[1]==0 and len(rows(fd))==2
    finally:
        try:os.write(exit_write,b'x')
        except BrokenPipeError:pass
        os.close(exit_write);os.close(read);child_status=os.waitpid(child,0)[1]
    assert child_status==0,child_status
    assert add(fd,paths[2])[0]>=0;os.close(fd)
    proof.append(dict(case='unreadable-peers-do-not-block-local-policy',passed=True,uid_census_scans=0,peer_setup='watch-before-drop-dumpability',peer_ready=peer_status,peer_fdinfo_errno=peer_access_errno,parent_watch_count_after=3))
    # Timing includes live self scans and kernel allocation, 512 distinct dirs.
    config(lock,cap=512);fd=init();times=[]
    for path in paths[:512]:
        start=time.perf_counter_ns();assert add(fd,path)[0]>=0;times.append((time.perf_counter_ns()-start)/1e6)
    before=stats();denial=[]
    for _ in range(300):
        start=time.perf_counter_ns();assert add(fd,paths[512])==(-1,errno.ENOSPC);denial.append((time.perf_counter_ns()-start)/1e6)
    after=stats();assert after[0]==before[0]and after[1]==before[1]
    assert add(fd,paths[0],CREATE|MASK_ADD)==(-1,errno.ENOSPC)
    remove_wd=int(rows(fd)[0].split()[1].split(':')[1],16)
    # Pick an inode different from paths[0] so the following update is stable.
    target_inode=paths[0].stat().st_ino
    remove_wd=next(int(line.split()[1].split(':')[1],16)for line in rows(fd)if int(line.split()[2].split(':')[1],16)!=target_inode)
    assert g.inotify_rm_watch(fd,remove_wd)==0 and len(rows(fd))==511
    updates=[]
    for _ in range(30):
        start=time.perf_counter_ns();assert add(fd,paths[0],CREATE|MASK_ADD)[0]>=0;updates.append((time.perf_counter_ns()-start)/1e6)
    os.close(fd)
    def summary(values):return dict(samples=len(values),total_ms=sum(values),median_ms=statistics.median(values),p95_ms=sorted(values)[int((len(values)-1)*.95)],maximum_ms=max(values))
    proof.append(dict(case='scan-cost-512',passed=True,adds=summary(times),adds_first32=summary(times[:32]),adds_last32=summary(times[-32:]),local_denials=summary(denial),existing_updates_below_cap=summary(updates),existing_update_at_cap="ENOSPC",full_self_scans_on_300_local_denials=after[0]-before[0],uid_rescans_on_300_local_denials=after[1]-before[1]))
print(json.dumps(dict(passed=True,production_accepted=False,uid=os.getuid(),kernel=os.uname().release,scope='VM local-only native prototype; live self fdinfo, conservative FD references, no peer census/global UID quota/sysctl/RPM/runtime edits',cases=proof),indent=2))
