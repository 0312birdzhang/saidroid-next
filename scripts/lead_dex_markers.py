#!/usr/bin/env python3
"""列 dex 里的标记字符串，证明每个候选版到底带了什么改动。"""
import sys
import zipfile

COMPONENTS = [
    "/var/tmp/saidroid-next-api29-component-diag2",
    "/var/tmp/saidroid-next-api29-component-r64",
    "/var/tmp/saidroid-next-api29-component-20261026-r63",
]
MARKERS = [
    b"SDVIEWS=", b"windowClients", b"ERROR_NO_RENDERER", b"error_no_renderer",
    b"unsupported|", b"SAILDROID_COMPOSE_ON_VSYNC", b"SAILDROID_NO_FASTPATH",
    b"layer_full", b"layer_identity", b"composes", b"SDDIAGNOSTICS=display",
    b"WPE bridge not connected", b"fast_path",
]

for comp in COMPONENTS:
    jar = comp + "/root/lib/runtime.jar"
    print("=== " + comp)
    try:
        with zipfile.ZipFile(jar) as z:
            print("jar_entries=%d" % len(z.namelist()))
            dex = z.read("classes.dex")
    except FileNotFoundError:
        print("MISSING " + jar)
        continue
    print("dex_bytes=%d" % len(dex))
    for m in MARKERS:
        print("marker %-28s %d" % (m.decode(), dex.count(m)))
    sys.stdout.flush()
