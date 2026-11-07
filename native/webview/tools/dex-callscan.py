#!/usr/bin/env python3
"""Find which classes in a dex call a given android.view.View method.

Why: QQ's content area stays white and ViewDelegate.onDraw never runs. The framework
bytecode says WebView.onDraw is the only paint path, so either PFLAG_SKIP_DRAW was set
on that view (View.setWillNotDraw), the view is not VISIBLE (View.setVisibility), or it
is not in the drawn hierarchy. This scans QQ's own dex files for call sites of those
methods so we know who could have set the flag, before spending a device window.

This is a *lead*, not proof: instructions are found by scanning code_item insns for
invoke-* opcodes (0x6e-0x78), which can also match literal data. Every hit is resolved
through method_ids, so a reported hit at least names a real View method reference.
"""
import struct, sys, os
from pathlib import Path

# Match by method *name* on any android.view/webkit/widget owner: d8 often keeps the
# static receiver type, so `webview.setVisibility(8)` can reference WebView or a
# subclass instead of View, and an exact-owner match silently misses it.
TARGET_NAMES = {
    'setWillNotDraw', 'setVisibility', 'setLayoutParams', 'setAlpha', 'setLayerType',
    'addView', 'addViewInLayout', 'attachViewToParent',
}
OWNER_PREFIXES = ('Landroid/view/', 'Landroid/webkit/', 'Landroid/widget/')

def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def uleb(b, o):
    r = s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s
        if not x & 0x80: return r, o
        s += 7

class Dex:
    def __init__(self, data):
        self.d = data
        (self.string_ids_size, self.string_ids_off, self.type_ids_size, self.type_ids_off,
         self.proto_ids_size, self.proto_ids_off, self.field_ids_size, self.field_ids_off,
         self.method_ids_size, self.method_ids_off, self.class_defs_size,
         self.class_defs_off) = struct.unpack_from('<12I', data, 56)
        self._strings = {}
        self._types = {}
        self._methods = {}

    def string(self, i):
        if i in self._strings: return self._strings[i]
        off = u32(self.d, self.string_ids_off + 4 * i)
        n, p = uleb(self.d, off)
        end = self.d.index(b'\x00', p)
        s = self.d[p:end].decode('utf-8', 'replace')
        self._strings[i] = s
        return s

    def type_name(self, i):
        if i in self._types: return self._types[i]
        name = self.string(u32(self.d, self.type_ids_off + 4 * i))
        self._types[i] = name
        return name

    def method(self, i):
        if i in self._methods: return self._methods[i]
        cls = self.type_name(u16(self.d, self.method_ids_off + 8 * i))
        proto = u16(self.d, self.method_ids_off + 8 * i + 2)
        name = self.string(u32(self.d, self.method_ids_off + 8 * i + 4))
        self._methods[i] = (cls, name)
        return self._methods[i]

    def classes(self):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32 * i
            class_idx = u32(self.d, off)
            data_off = u32(self.d, off + 24)
            yield self.type_name(class_idx), data_off

    def caller_methods(self, data_off, class_name):
        """Yield (method_name, code_off) for one class_data_item."""
        if not data_off: return
        o = data_off
        sf, o = uleb(self.d, o)
        inf, o = uleb(self.d, o)
        dm, o = uleb(self.d, o)
        vm, o = uleb(self.d, o)
        for _ in range(sf + inf):
            _, o = uleb(self.d, o); _, o = uleb(self.d, o)
        for kind, count in (('direct', dm), ('virtual', vm)):
            midx = 0
            for _ in range(count):
                diff, o = uleb(self.d, o)
                _, o = uleb(self.d, o)
                code_off, o = uleb(self.d, o)
                midx += diff
                if code_off:
                    yield kind, self.method(midx)[1], code_off

def scan(path, hits):
    d = Dex(Path(path).read_bytes())
    for class_name, data_off in d.classes():
        if not data_off: continue
        for kind, mname, code_off in d.caller_methods(data_off, class_name):
            if not code_off: continue
            insns_size = u32(d.d, code_off + 12)
            insns_off = code_off + 16
            n = min(insns_size, (len(d.d) - insns_off) // 2)
            for k in range(n - 1):
                op = u16(d.d, insns_off + 2 * k)
                if 0x6e <= op <= 0x78:
                    midx = u16(d.d, insns_off + 2 * (k + 1))
                    if midx >= d.method_ids_size: continue
                    cls, name = d.method(midx)
                    if name in TARGET_NAMES and cls.startswith(OWNER_PREFIXES):
                        hits.setdefault((cls, name), set()).add((class_name, mname, kind))
    return d

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return 2
    hits = {}
    for p in args:
        scan(p, hits)
    for (cls, name), callers in sorted(hits.items()):
        print(f'== {cls}->{name}: {len(callers)} call sites')
        for c, m, kind in sorted(callers)[:40]:
            print(f'   {c}::{m} ({kind})')
    if not hits:
        print('NO_CALL_SITES')
    return 0

if __name__ == '__main__':
    sys.exit(main())
