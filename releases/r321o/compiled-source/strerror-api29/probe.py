"""Exercise Android ABI relocations through the actual Bionic linker."""
from pathlib import Path
import ctypes,os,sys,json,concurrent.futures
lib,linker,fixture,mode=sys.argv[1:]
ctypes.CDLL(lib,mode=ctypes.RTLD_GLOBAL)
l=ctypes.CDLL(linker,mode=ctypes.RTLD_GLOBAL)
load=l.bionic_dlopen;load.restype=ctypes.c_void_p;load.argtypes=[ctypes.c_char_p,ctypes.c_int]
sym=l.bionic_dlsym;sym.restype=ctypes.c_void_p;sym.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
add=l.bionic_add_library_path;add.argtypes=[ctypes.c_char_p];assert add(str(Path(fixture).parent).encode())==0
h=load(Path(fixture).name.encode(),os.RTLD_NOW)
if not h:
 l.bionic_dlerror.restype=ctypes.c_char_p
 raise RuntimeError(l.bionic_dlerror())
f=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_char_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_int))(sym(h,b'query_error'))
def query(number,size):
 buf=ctypes.create_string_buffer(b'Z'*1025,1026);after=ctypes.c_int();result=f(number,buf,size,ctypes.byref(after));return result,buf.raw,after.value
if mode=='negative':
 result,buf,after=query(2,1024)
 assert result!=0 or buf.split(b'\0')[0]!=b'No such file or directory'
 print(json.dumps(dict(expected_failure=True,result=result,buffer_written=buf[:1]!=b'Z')));sys.exit()
cases=[(0,b'Success'),(2,b'No such file or directory'),(13,b'Permission denied'),(-17,b'Unknown error -17'),(2147483647,b'Unknown error 2147483647')]
checks=0
for number,message in cases:
 for size in [0,1,4,len(message),len(message)+1,1024]:
  result,buf,after=query(number,size);truncated=len(message)>=size
  assert result==(-1 if truncated else 0),(number,size,result)
  assert after==(34 if truncated else 123),(number,size,after)
  expected=message[:max(0,size-1)]+b'\0' if size else b''
  assert buf[:len(expected)]==expected,(number,size,buf[:60])
  assert buf[size:]==b'Z'*(1025-size)+b'\0','buffer boundary overwritten'
  checks+=1
def worker(index):
 for j in range(200):
  number,message=cases[(index+j)%len(cases)];result,buf,after=query(number,1024)
  assert result==0 and after==123 and buf.split(b'\0')[0]==message
 return 200
with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:thread_checks=sum(pool.map(worker,range(8)))
print(json.dumps(dict(passed=True,checks=checks,thread_checks=thread_checks,real_bionic_relocation=True,errno_and_bounds=True)))
