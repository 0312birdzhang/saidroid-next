#!/usr/bin/env python3
"""Static survey of what an APK's dex code references on the android.webkit surface.

Answers three questions the WebView provider contract depends on (Lead's ②):
  1. which `android.webkit.WebSettings` methods does the app actually call  -> our
     Settings must implement all of them (javac enforces the abstract ones; this
     proves the concrete list the app touches);
  2. which `android.webkit.WebView` / `CookieManager` methods are referenced
     -> each one must exist on our provider proxy (or be provably unreachable);
  3. which classes extend WebViewClient and define `onReceivedError`, and with
     which descriptor -> decides whether the legacy or the API23 overload is the
     one the app overrides.

Usage: dex-webview-usage.py <apk-or-dex>...   (read-only; only method tables and
class_data are parsed, code items are never decoded).
"""
import sys, zipfile, struct

INTEREST = {
    "Landroid/webkit/WebSettings;": "settings",
    "Landroid/webkit/WebView;": "webview",
    "Landroid/webkit/CookieManager;": "cookies",
    "Landroid/webkit/WebChromeClient;": "chrome",
    "Landroid/webkit/WebViewClient;": "client",
}

def uleb(buf, off):
    result = shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80):
            return result, off
        shift += 7

class Dex:
    def __init__(self, data):
        self.b = memoryview(data)
        # header: 56 string_ids{size,off} 64 type_ids 72 proto_ids 80 field_ids 88 method_ids 96 class_defs
        (self.string_ids_size, self.string_ids_off,
         self.type_ids_size, self.type_ids_off,
         self.proto_ids_size, self.proto_ids_off,
         _field_ids_size, _field_ids_off,
         self.method_ids_size, self.method_ids_off,
         self.class_defs_size, self.class_defs_off) = struct.unpack_from("<12I", self.b, 56)
        self._str = {}
        self._type = {}

    def string(self, i):
        s = self._str.get(i)
        if s is None:
            off = struct.unpack_from("<I", self.b, self.string_ids_off + 4 * i)[0]
            _, p = uleb(self.b, off)                       # utf16 length, unused
            end = self.b.obj.find(b"\x00", p)
            s = bytes(self.b[p:end]).decode("utf-8", "replace")
            self._str[i] = s
        return s

    def type_(self, i):
        t = self._type.get(i)
        if t is None:
            t = self.string(struct.unpack_from("<I", self.b, self.type_ids_off + 4 * i)[0])
            self._type[i] = t
        return t

    def method(self, i):
        off = self.method_ids_off + 8 * i
        class_idx, proto_idx, name_idx = struct.unpack_from("<HHI", self.b, off)
        return self.type_(class_idx), self.string(name_idx), proto_idx

    def proto_desc(self, proto_idx):
        """Return the descriptor tail, e.g. (ILjava/lang/String;)V."""
        _, return_type_idx, params_off = struct.unpack_from("<III", self.b,
                                                            self.proto_ids_off + 12 * proto_idx)
        parts = []
        if params_off:
            size = struct.unpack_from("<I", self.b, params_off)[0]
            for k in range(size):
                parts.append(self.type_(struct.unpack_from("<H", self.b, params_off + 4 + 2 * k)[0]))
        return "(" + "".join(parts) + ")" + self.type_(return_type_idx)

    def classes(self):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32 * i
            class_idx, access, super_idx, _ifaces, _src, _anno, class_data_off, _sv = \
                struct.unpack_from("<IIIIIIII", self.b, off)
            yield self.type_(class_idx), (self.type_(super_idx) if super_idx != 0xffffffff else None), class_data_off

    def defined_methods(self, class_data_off):
        """Yield (name, proto_idx) for every method the class defines."""
        if not class_data_off:
            return
        p = class_data_off
        sf, p = uleb(self.b, p)
        inf, p = uleb(self.b, p)
        dm, p = uleb(self.b, p)
        vm, p = uleb(self.b, p)
        for _ in range(sf + inf):                     # field idx delta + access flags
            _, p = uleb(self.b, p); _, p = uleb(self.b, p)
        for count in (dm, vm):
            idx = 0
            for _ in range(count):
                diff, p = uleb(self.b, p)
                access, p = uleb(self.b, p)
                code_off, p = uleb(self.b, p)
                idx += diff
                off = self.method_ids_off + 8 * idx
                class_idx, proto_idx, name_idx = struct.unpack_from("<HHI", self.b, off)
                yield self.string(name_idx), proto_idx

def dex_blobs(path):
    if path.endswith(".dex"):
        yield path, open(path, "rb").read()
        return
    with zipfile.ZipFile(path) as z:
        for n in sorted(z.namelist()):
            if n.endswith(".dex"):
                yield n, z.read(n)

def main(paths):
    refs = {k: {} for k in INTEREST.values()}
    super_of = {}
    client_defs = []          # (class, superclass, [(name, desc)])
    for path in paths:
        for name, data in dex_blobs(path):
            d = Dex(data)
            for i in range(d.method_ids_size):
                cls, mname, proto_idx = d.method(i)
                bucket = INTEREST.get(cls)
                if bucket:
                    refs[bucket].setdefault(mname, set()).add(d.proto_desc(proto_idx))
            for cls, sup, cdo in d.classes():
                super_of[cls] = sup
            for cls, sup, cdo in d.classes():
                # classes that (transitively) extend WebViewClient
                cur, depth = sup, 0
                while cur and depth < 8 and cur not in ("Ljava/lang/Object;",):
                    if cur == "Landroid/webkit/WebViewClient;":
                        defs = [(n, d.proto_desc(p)) for n, p in d.defined_methods(cdo)
                                if n in ("onReceivedError", "onReceivedHttpError",
                                         "shouldOverrideUrlLoading", "onPageFinished",
                                         "onPageStarted")]
                        client_defs.append((cls, sup, depth + 1, name, defs))
                        break
                    cur = super_of.get(cur)
                    depth += 1

    print("== dex files scanned:", len(paths))
    for bucket in ("settings", "webview", "cookies", "chrome", "client"):
        names = sorted(refs[bucket])
        print("\n== %s: %d distinct methods referenced" % (bucket.upper(), len(names)))
        for n in names:
            descs = sorted(refs[bucket][n])
            print("   %-46s %s" % (n, " | ".join(descs[:2])))

    print("\n== classes extending WebViewClient that define webview callbacks:", len(client_defs))
    for cls, sup, depth, dexname, defs in client_defs[:40]:
        print("   %s (super=%s depth=%d dex=%s)" % (cls, sup, depth, dexname))
        for n, desc in defs:
            print("       %s%s" % (n, desc))

if __name__ == "__main__":
    main(sys.argv[1:] or ["test/qq.apk"])
