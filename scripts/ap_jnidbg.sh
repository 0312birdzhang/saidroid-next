python3 - <<'PY'
import struct
p='/tmp/shimtest/libandroid_runtime.so'
d=open(p,'rb').read()
print('size', len(d))
i=d.find(b'nativeSetDataSize\x00')
print('raw offset of string:', hex(i) if i>=0 else 'not found')
e_shoff=struct.unpack_from('<Q',d,0x28)[0]
e_shentsize=struct.unpack_from('<H',d,0x3A)[0]
e_shnum=struct.unpack_from('<H',d,0x3C)[0]
e_shstrndx=struct.unpack_from('<H',d,0x3E)[0]
print('shoff',hex(e_shoff),'num',e_shnum,'shstrndx',e_shstrndx)
raw=[]
for k in range(e_shnum):
    off=e_shoff+k*e_shentsize
    vals=struct.unpack_from('<IIQQQQ',d,off)
    raw.append(vals)
shstr=raw[e_shstrndx]
base=shstr[4]
for v in raw:
    name_off=base+v[0]
    end=d.index(b'\x00',name_off)
    nm=d[name_off:end].decode('utf-8','replace')
    print('%-20s type=%d addr=0x%x off=0x%x size=0x%x'%(nm,v[1],v[3],v[4],v[5]))
PY
