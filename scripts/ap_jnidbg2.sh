cd /media/psf/Home/WorkSpace/saidroid-next/scripts/debug
python3 - <<'PY'
import sys
sys.path.insert(0,'.')
from jnimethods import Elf64
e = Elf64('/tmp/shimtest/libandroid_runtime.so')
va = e.find_cstr_vaddr('nativeSetDataSize')
print('string vaddr =', hex(va) if va else None)
print('rela entries =', len(e.rela))
hits = e.find_ptrs_to(va) if va else []
print('ptr hits =', [hex(h) for h in hits][:5])
if hits:
    h = hits[0]
    print('entry name=', e.cstr(e.qword(h)))
    print('sig ptr =', hex(e.qword(h+8) or 0), 'sig =', e.cstr(e.qword(h+8)))
PY
