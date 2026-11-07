cd /media/psf/Home/WorkSpace/saidroid-next/scripts/debug
python3 - <<'PY'
import sys, struct
sys.path.insert(0,'.')
from jnimethods import Elf64
e = Elf64('/tmp/shimtest/libandroid_runtime.so')
# 1) 找所有出现 nativeSetDataSize 的偏移
i=0; occ=[]
while True:
    i=e.d.find(b'nativeSetDataSize', i)
    if i<0: break
    occ.append((i, e.off_to_vaddr(i), e.d[i-8:i+40]))
    i+=1
for o,va,ctx in occ[:4]:
    print('off=%#x va=%s ctx=%r'%(o, hex(va) if va else None, ctx))
# 2) .rela.dyn 里 addend 等于该 vaddr 的
if occ and occ[0][1]:
    target=occ[0][1]
    hits=[(off,add) for off,add in e.rela.items() if add==target]
    print('rela hits for target:', [(hex(o),hex(a)) for o,a in hits][:5])
# 3) 看 .data.rel.ro 开头的内容
sec=[s for s in e.sections if s['name']=='.data.rel.ro'][0]
print('.data.rel.ro addr=%#x off=%#x size=%#x'%(sec['addr'],sec['off'],sec['size']))
for k in range(0, 96, 8):
    va=sec['addr']+k
    raw=struct.unpack_from('<Q', e.d, sec['off']+k)[0]
    eff=e.qword(va)
    print('  slot %#x raw=%#x eff=%#x str=%s'%(va, raw, eff or 0, e.cstr(eff) if eff else ''))
PY
