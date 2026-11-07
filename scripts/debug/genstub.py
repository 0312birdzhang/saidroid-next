#!/usr/bin/env python3
"""给 Android 的 AIDL 接口生成一个「全空实现」的 Stub 子类。

背景：AIDL 生成的 `IFoo.Stub` 并没有实现接口方法，要用的类必须自己把几十个方法
全写出来。我们跑的是单进程独立运行时，没有 system_server，只需要其中少数几个方法
有真实行为，其余全是 no-op。手写 79 个方法没意义，用这个脚本生成。

用法：
    genstub.py --javap <javap> --cp <classpath> --iface <接口全名> \
               --class <生成的类名> --out <输出 .java 路径> [--package <包名>]

生成后按需把个别方法改成有意义的实现（脚本会在文件头写明这一点）。
"""
import argparse
import re
import subprocess
import sys

PRIMITIVE_DEFAULTS = {
    'void': None,
    'boolean': 'false',
    'byte': '0',
    'short': '0',
    'int': '0',
    'long': '0L',
    'char': '0',
    'float': '0.0f',
    'double': '0.0',
}

# 返回类型里可能有泛型（java.util.List<android.content.pm.ResolveInfo>），
# 所以 ret 用非贪婪的 .+?，靠「最后一个标识符 + 左括号」来定位方法名。
METHOD_RE = re.compile(
    r'^\s+public\s+abstract\s+(?P<ret>.+?)\s+(?P<name>\w+)\((?P<params>.*)\)'
    r'(\s+throws\s+[\w\.,\s<>\$\[\]]+)?;\s*$')


def parse_methods(text):
    out = []
    for line in text.splitlines():
        if 'abstract' not in line:
            continue
        m = METHOD_RE.match(line)
        if not m:
            continue
        params = m.group('params').strip()
        out.append((m.group('ret'), m.group('name'), params))
    return out


def split_params(params):
    """按顶层逗号切参数类型；android 的 AIDL 里偶有 List<T>，要跳过尖括号里的逗号"""
    out = []
    depth = 0
    cur = ''
    for ch in params:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def with_names(params):
    """把 "int, java.lang.String" 变成 "int arg0, java.lang.String arg1" """
    parts = split_params(params)
    return ', '.join('%s arg%d' % (ty, i) for i, ty in enumerate(parts))


def default_for(ret):
    if ret in PRIMITIVE_DEFAULTS:
        return PRIMITIVE_DEFAULTS[ret]
    return 'null'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--javap', required=True)
    ap.add_argument('--cp', required=True)
    ap.add_argument('--iface', required=True)
    ap.add_argument('--class', dest='cls', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--package', default=None)
    ap.add_argument('--comment', default='')
    args = ap.parse_args()

    text = subprocess.run([args.javap, '-p', '-classpath', args.cp, args.iface],
                          capture_output=True, text=True).stdout
    methods = parse_methods(text)
    if not methods:
        print('没解析到方法，javap 输出：\n' + text[:800], file=sys.stderr)
        return 1

    buf = []
    if args.package:
        buf.append('package %s;\n' % args.package)
    buf.append('/* 由 genstub.py 生成：%s 的空实现。' % args.iface)
    buf.append(' *')
    buf.append(' * 只有少数方法需要真实行为，其余按 AIDL 语义返回 0/false/null。')
    buf.append(' * 改动时请保留下面 @Override 的顺序，方便对着 javap 核对。')
    if args.comment:
        buf.append(' * ' + args.comment)
    buf.append(' */')
    buf.append('public class %s extends %s.Stub {' % (args.cls, args.iface))
    for ret, name, params in methods:
        d = default_for(ret)
        buf.append('')
        buf.append('    @Override')
        named = with_names(params)
        if ret == 'void':
            buf.append('    public void %s(%s) {' % (name, named))
            buf.append('    }')
        else:
            buf.append('    public %s %s(%s) {' % (ret, name, named))
            buf.append('        return %s;' % d)
            buf.append('    }')
    buf.append('}')
    open(args.out, 'w').write('\n'.join(buf) + '\n')
    print('生成 %s：%d 个方法 -> %s' % (args.cls, len(methods), args.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
