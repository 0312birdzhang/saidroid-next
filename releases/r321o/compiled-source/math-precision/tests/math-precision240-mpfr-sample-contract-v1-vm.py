from pathlib import Path
import ctypes,hashlib,json,math,random,struct
class Mpfr(ctypes.Structure):_fields_=[('precision',ctypes.c_long),('sign',ctypes.c_int),('exponent',ctypes.c_long),('limbs',ctypes.c_void_p)]
m=ctypes.CDLL('libmpfr.so.6');P=ctypes.POINTER(Mpfr)
m.mpfr_init2.argtypes=[P,ctypes.c_long];m.mpfr_clear.argtypes=[P];m.mpfr_set_d.argtypes=[P,ctypes.c_double,ctypes.c_int];m.mpfr_get_d.argtypes=[P,ctypes.c_int];m.mpfr_get_d.restype=ctypes.c_double;m.mpfr_get_version.restype=ctypes.c_char_p
root=Path('/var/tmp/saidroid-application-temp-startup237-v1-formal-vm-component/root');backend=ctypes.CDLL(str(root/'lib/libsdstrictmath-fdlibm.so'),mode=ctypes.RTLD_GLOBAL);companion=Path('/var/tmp/saidroid-math-precision240-companion-v1/libsdmath-precision.so');lib=ctypes.CDLL(str(companion))
names=['sin','cos','tan','cbrt','pow'];rng=random.Random(240);inputs=[0.0,-0.0,math.inf,-math.inf,math.nan,5.319372648326541E255,-5.319372648326541E255,1.0,-1.0,math.pi/2,-math.pi/2,math.nextafter(math.pi/2,math.inf),math.nextafter(math.pi/2,0),2**-1074,-2**-1074,1e300,-1e300,27.0,-27.0,-8.605787237358564E307]
while len(inputs)<4116:
 x=struct.unpack('<d',struct.pack('<Q',rng.getrandbits(64)))[0]
 if math.isfinite(x):inputs.append(x)
a,b,c=Mpfr(),Mpfr(),Mpfr()
for v in [a,b,c]:m.mpfr_init2(ctypes.byref(v),4096)
worst={};fails=[];raw=[];counts={}
try:
 for name in names:
  f=getattr(lib,'Math_'+name);f.argtypes=[ctypes.c_double]*(2 if name=='pow'else 1);f.restype=ctypes.c_double
  op=getattr(m,'mpfr_'+name);op.argtypes=[P,P]+([P]if name=='pow'else[])+[ctypes.c_int]
  pairs=[(x,0.0)for x in inputs]if name!='pow'else[(0.0,2.0),(-0.0,3.0),(-0.0,-3.0),(math.inf,-1.0),(-math.inf,3.0),(-2.0,.5),(math.nan,0.0),(3.0000000000000004,2.1)]
  if name=='pow':
   for i in range(4096):
    x=struct.unpack('<d',struct.pack('<Q',rng.getrandbits(64)&0x7fefffffffffffff))[0]; y=rng.uniform(-16,16)
    pairs.append((x,y))
   pairs += [(-abs(x),float(y))for x,y in [(2,3),(2,-3),(1,4097),(1,-4097),(.5,1025),(10,17),(1e300,2)]]
  worst[name]=0.;counts[name]=len(pairs)
  for x,y in pairs:
   actual=f(x,y)if name=='pow'else f(x);m.mpfr_set_d(ctypes.byref(a),x,0);m.mpfr_set_d(ctypes.byref(c),y,0);op(ctypes.byref(b),ctypes.byref(a),*([ctypes.byref(c)]if name=='pow'else[]),0);expected=m.mpfr_get_d(ctypes.byref(b),0)
   if math.isnan(expected):ok=math.isnan(actual);err=0.
   elif expected==0 or math.isinf(expected):ok=struct.pack('<d',expected)==struct.pack('<d',actual);err=0.
   else:err=abs(actual-expected)/math.ulp(expected);ok=math.isfinite(actual)and err<=1.
   worst[name]=max(worst[name],err)
   if not ok:fails.append(dict(function=name,input=x,exponent=y,actual=actual,expected=expected,error_ulps=err))
   raw.append([name]+[struct.pack('<d',v).hex()for v in [x,y,actual,expected]])
 record=dict(scope='Independent MPFR4096 oracle for actual component-private five Math entries; finite random binary64, huge arguments, subnormal, signed zero, exact cubes and real pow domains. Native algorithm contract only, not phone/full CTS. Java-specific pow(1,NaN) checked separately in ART contract.',passed=not fails,samples=sum(counts.values()),counts=counts,functions=names,random_seed=240,mpfr_version=m.mpfr_get_version().decode(),precision_bits=4096,max_error_ulps=worst,failures=fails,companion_sha256=hashlib.sha256(companion.read_bytes()).hexdigest(),backend_sha256=hashlib.sha256((root/'lib/libsdstrictmath-fdlibm.so').read_bytes()).hexdigest(),input_result_bits_sha256=hashlib.sha256(json.dumps(raw).encode()).hexdigest())
 out=Path('/media/psf/Home/WorkSpace/saidroid-next/build/evidence/cts-frame-repair-20261031/math-precision240-mpfr-sample-contract-v1.json');assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));assert not fails
finally:
 for v in [a,b,c]:m.mpfr_clear(ctypes.byref(v))
