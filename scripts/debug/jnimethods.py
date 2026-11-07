#!/usr/bin/env python3
"""从 .so 的 JNINativeMethod 表里抠出 {名字, 签名}。

JNINativeMethod = { const char *name; const char *signature; void *fnPtr; }，24 字节。
用法：
    jnimethods.py <lib.so> <方法名> [更多方法名...]
    jnimethods.py <lib.so> --scan native     # 把所有以 native 开头的都打出来
目的：Java 类和 native 注册表对不上时（报 "no static or non-static method"），
先看 native 侧到底要什么签名，再去改 Java 类或确认版本差异。
"""
import struct
import sys


class Elf64:
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        if self.d[:4] != b'\x7fELF':
            raise SystemExit('不是 ELF')
        if self.d[4] != 2:
            raise SystemExit('只支持 ELF64')
        e_shoff = struct.unpack_from('<Q', self.d, 0x28)[0]
        e_shentsize = struct.unpack_from('<H', self.d, 0x3A)[0]
        e_shnum = struct.unpack_from('<H', self.d, 0x3C)[0]
        e_shstrndx = struct.unpack_from('<H', self.d, 0x3E)[0]
        raw = []
        for i in range(e_shnum):
            off = e_shoff + i * e_shentsize
            sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size = \
                struct.unpack_from('<IIQQQQ', self.d, off)
            raw.append([sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size])
        shstr = raw[e_shstrndx]
        self.sections = []
        for sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size in raw:
            name_off = shstr[4] + sh_name
            end = self.d.index(b'\x00', name_off)
            self.sections.append({
                'name': self.d[name_off:end].decode('utf-8', 'replace'),
                'type': sh_type, 'addr': sh_addr,
                'off': sh_offset, 'size': sh_size,
            })
        self._load_rela()

    def _load_rela(self):
        """aarch64 用 RELA：.data.rel.ro 里的指针文件里是 0，真值在重定位的 addend 里。
        解析 .rela.dyn 建 offset->addend 映射，才能还原表里的指针。"""
        self.rela = {}
        for s in self.sections:
            if s['type'] != 4:      # SHT_RELA
                continue
            n = s['size'] // 24
            for i in range(n):
                off = s['off'] + i * 24
                r_offset, r_info, r_addend = struct.unpack_from('<QQq', self.d, off)
                self.rela[r_offset] = r_addend

    def qword(self, va):
        """按加载后的实际值读一个 8 字节指针"""
        if va in self.rela:
            return self.rela[va]
        off = self.vaddr_to_off(va)
        if off is None:
            return None
        return struct.unpack_from('<Q', self.d, off)[0]

    def vaddr_to_off(self, va):
        for s in self.sections:
            if s['addr'] and s['type'] != 8 and s['addr'] <= va < s['addr'] + s['size']:
                return s['off'] + (va - s['addr'])
        return None

    def off_to_vaddr(self, off):
        for s in self.sections:
            if s['addr'] and s['off'] <= off < s['off'] + s['size']:
                return s['addr'] + (off - s['off'])
        return None

    def cstr(self, va):
        off = self.vaddr_to_off(va)
        if off is None or off >= len(self.d):
            return None
        end = self.d.find(b'\x00', off, off + 256)
        if end < 0:
            return None
        try:
            return self.d[off:end].decode('utf-8')
        except UnicodeDecodeError:
            return None

    def find_cstr_vaddr(self, text):
        """在可读段里找字符串，返回它的 vaddr（取第一个）"""
        needle = text.encode() + b'\x00'
        start = 0
        while True:
            i = self.d.find(needle, start)
            if i < 0:
                return None
            va = self.off_to_vaddr(i)
            if va is not None:
                return va
            start = i + 1

    def find_ptrs_to(self, va):
        """找出所有「加载后等于 va」的 8 字节槽位（按 vaddr 返回）"""
        out = []
        for s in self.sections:
            if not s['addr'] or s['type'] != 1:
                continue
            for k in range(0, s['size'] - 7, 8):
                cand = s['addr'] + k
                if self.qword(cand) == va:
                    out.append(cand)
        return out


def entry_for(elf, name):
    nva = elf.find_cstr_vaddr(name)
    if nva is None:
        return None
    hits = elf.find_ptrs_to(nva)
    # JNINativeMethod 表里 name 后面紧跟 signature
    for va in hits:
        off = elf.vaddr_to_off(va)
        if off is None or off + 24 > len(elf.d):
            continue
        sig_va = elf.qword(va + 8)
        fn_va = elf.qword(va + 16)
        if sig_va is None or fn_va is None:
            continue
        sig = elf.cstr(sig_va)
        if sig and sig.startswith('('):
            return name, sig, fn_va
    return None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    elf = Elf64(sys.argv[1])
    args = sys.argv[2:]
    if args[0] == '--scan':
        prefix = args[1] if len(args) > 1 else 'native'
        seen = set()
        for s in elf.sections:
            if not s['addr'] or s['type'] == 8:
                continue
            blob = elf.d[s['off']:s['off'] + s['size']]
            i = 0
            while True:
                i = blob.find(prefix.encode(), i)
                if i < 0:
                    break
                end = blob.find(b'\x00', i)
                if end < 0:
                    break
                name = blob[i:end].decode('utf-8', 'replace')
                i = end + 1
                if name in seen or not name.replace('_', '').isalnum():
                    continue
                seen.add(name)
        for name in sorted(seen):
            r = entry_for(elf, name)
            if r:
                print('%-40s %s' % (r[0], r[1]))
        return 0
    for name in args:
        r = entry_for(elf, name)
        print('%-40s %s' % (name, r[1] if r else '(表里没找到)'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
