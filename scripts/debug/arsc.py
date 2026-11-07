#!/usr/bin/env python3
"""解析 APK 里的 resources.arsc，导出 name -> resource id。

为什么需要：这个运行时里 Resources.getIdentifier(name, type, pkg) 返回 0
（框架资源也一样），所以拿不到按名字查的 id。而 LayoutInflater.inflate 必须要 id。
那就自己把 arsc 解出来，把 (type, name) -> id 的表建好。

资源 id 布局：0xPPTTEEEE
    PP = package id（通常 0x7f）
    TT = type id（从 package 里的 type 字符串表里的顺序得到）
    EEEE = entry 下标

用法：
    arsc.py <apk 或 resources.arsc> --list layout [前缀过滤]
    arsc.py <apk> --id layout main_tab
    arsc.py <apk> --summary
"""
import struct
import sys
import zipfile

CHUNK_STRING_POOL = 0x0001
CHUNK_TABLE = 0x0002
CHUNK_TABLE_PACKAGE = 0x0200
CHUNK_TABLE_TYPE = 0x0201
CHUNK_TABLE_TYPE_SPEC = 0x0202

UTF8_FLAG = 0x100


class Reader:
    def __init__(self, data):
        self.d = data

    def u8(self, off):
        return self.d[off]

    def u16(self, off):
        return struct.unpack_from('<H', self.d, off)[0]

    def u32(self, off):
        return struct.unpack_from('<I', self.d, off)[0]

    def chunk(self, off):
        t = self.u16(off)
        hs = self.u16(off + 2)
        size = self.u32(off + 4)
        return t, hs, size


def parse_string_pool(r, off):
    """返回字符串列表"""
    t, hs, size = r.chunk(off)
    assert t == CHUNK_STRING_POOL, 'not a string pool: 0x%04x' % t
    count = r.u32(off + 8)
    flags = r.u32(off + 16)
    strings_start = r.u32(off + 20)
    utf8 = bool(flags & UTF8_FLAG)
    out = []
    base = off + strings_start
    for i in range(count):
        so = r.u32(off + hs + i * 4)
        p = base + so
        if utf8:
            # 两段长度（UTF-16 长度、UTF-8 字节长度），都为 1 或 2 字节
            p2 = p
            n = r.u8(p2)
            if n & 0x80:
                p2 += 1
            p2 += 1
            ln = r.u8(p2)
            if ln & 0x80:
                ln = ((ln & 0x7f) << 8) | r.u8(p2 + 1)
                p2 += 1
            p2 += 1
            out.append(r.d[p2:p2 + ln].decode('utf-8', 'replace'))
        else:
            ln = r.u16(p)
            if ln & 0x8000:
                ln = ((ln & 0x7fff) << 16) | r.u16(p + 2)
                p += 2
            p += 2
            out.append(r.d[p:p + ln * 2].decode('utf-16-le', 'replace'))
    return out


def parse_package(r, off):
    t, hs, size = r.chunk(off)
    assert t == CHUNK_TABLE_PACKAGE, 'not a package: 0x%04x' % t
    pkg_id = r.u32(off + 8)
    name_raw = r.d[off + 12:off + 12 + 256]
    name = name_raw.decode('utf-16-le', 'replace').split('\x00')[0]
    type_strings_off = r.u32(off + 268)
    key_strings_off = r.u32(off + 276)
    type_names = parse_string_pool(r, off + type_strings_off)
    key_names = parse_string_pool(r, off + key_strings_off)

    types = {}      # type_id -> {(name) : entry_count}，用来统计
    resources = {}  # (type_name, key_name) -> res_id
    counts = {}

    p = off + hs
    end = off + size
    entry_count_by_type = {}
    while p < end - 8:
        ct, chs, csz = r.chunk(p)
        if csz <= 0:
            break
        if ct == CHUNK_TABLE_TYPE:
            type_id = r.u8(p + 8)
            entry_count = r.u32(p + 12)
            entries_start = r.u32(p + 16)
            type_name = type_names[type_id - 1] if 0 < type_id <= len(type_names) else '?%d' % type_id
            for i in range(entry_count):
                eo = r.u32(p + chs + i * 4)
                if eo == 0xFFFFFFFF:
                    continue
                ep = p + entries_start + eo
                esize = r.u16(ep)
                eflags = r.u16(ep + 2)
                key_idx = r.u32(ep + 4)
                key = key_names[key_idx] if key_idx < len(key_names) else '?%d' % key_idx
                rid = (pkg_id << 24) | (type_id << 16) | i
                resources[(type_name, key)] = rid
                counts[type_name] = counts.get(type_name, 0) + 1
        p += csz
    return name, pkg_id, resources, counts


def load_arsc(path):
    if path.endswith('.apk'):
        with zipfile.ZipFile(path) as z:
            data = z.read('resources.arsc')
    else:
        data = open(path, 'rb').read()
    return data


def parse(path):
    r = Reader(load_arsc(path))
    t, hs, size = r.chunk(0)
    assert t == CHUNK_TABLE, 'not a resource table: 0x%04x' % t
    pkg_count = r.u32(8)
    packages = []
    p = hs
    while p < size - 8 and len(packages) < pkg_count:
        ct, chs, csz = r.chunk(p)
        if csz <= 0:
            break
        if ct == CHUNK_TABLE_PACKAGE:
            packages.append(parse_package(r, p))
        p += csz
    return packages


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    path = sys.argv[1]
    mode = sys.argv[2]
    pkgs = parse(path)
    if mode == '--summary':
        for name, pid, res, counts in pkgs:
            print('package %s id=0x%02x  资源条目 %d' % (name, pid, len(res)))
            for t, c in sorted(counts.items(), key=lambda kv: -kv[1])[:20]:
                print('   %-16s %d' % (t, c))
        return 0
    if mode == '--list':
        want = sys.argv[3] if len(sys.argv) > 3 else None
        filt = sys.argv[4].lower() if len(sys.argv) > 4 else ''
        for name, pid, res, counts in pkgs:
            for (t, k), rid in sorted(res.items(), key=lambda kv: kv[1]):
                if want and t != want:
                    continue
                if filt and filt not in k.lower():
                    continue
                print('0x%08x  %-12s %s' % (rid, t, k))
        return 0
    if mode == '--id':
        want, key = sys.argv[3], sys.argv[4]
        for name, pid, res, counts in pkgs:
            rid = res.get((want, key))
            if rid is None:
                print('找不到 %s/%s' % (want, key))
                return 1
            print('0x%08x' % rid)
            return 0
    print('未知模式')
    return 1


if __name__ == '__main__':
    sys.exit(main())
