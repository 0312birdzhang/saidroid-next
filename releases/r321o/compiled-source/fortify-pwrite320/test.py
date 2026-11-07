"""Exercise real positioned writes, errno and fortify termination."""
import ctypes,sys,os,resource,subprocess,tempfile,json,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CORE,(0,0));library=Path(sys.argv[1]);handle=ctypes.CDLL(str(library),use_errno=True)
def entry(name):
 f=getattr(handle,name);f.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int64,ctypes.c_size_t];f.restype=ctypes.c_ssize_t;return f
if len(sys.argv)>2:
 name,kind=sys.argv[2:];f=entry(name);data=ctypes.create_string_buffer(b'abcd');f(-1,data,5 if kind=='buffer'else 1<<63,0,4 if kind=='buffer'else ctypes.c_size_t(-1).value);raise AssertionError('fortify failed to abort')
rows=[]
for name in ['bionic___pwrite_chk','bionic___pwrite64_chk']:
 f=entry(name)
 with tempfile.TemporaryFile()as file:
  fd=file.fileno();os.write(fd,b'original');os.lseek(fd,3,os.SEEK_SET);data=ctypes.create_string_buffer(b'test');offset=(1<<32)+37
  assert f(fd,data,4,offset,4)==4 and os.pread(fd,4,offset)==b'test';assert os.lseek(fd,0,os.SEEK_CUR)==3;assert os.pread(fd,8,0)==b'original';assert f(fd,None,0,0,0)==0
  ctypes.set_errno(0);assert f(-1,data,4,0,4)==-1 and ctypes.get_errno()==9
  ctypes.set_errno(0);assert f(fd,data,4,-1,4)==-1 and ctypes.get_errno()==22
 for kind in ['buffer','count']:
  q=subprocess.run([sys.executable,__file__,str(library),name,kind],capture_output=True,timeout=6);assert q.returncode==-signal.SIGABRT,(name,kind,q.returncode,q.stderr)
 rows.append(dict(entry=name,sparse_offset=offset,position_unchanged=True,errno_checked=['EBADF','EINVAL'],fortify_abort=['buffer','count']))
print(json.dumps(dict(passed=True,cases=rows)))
