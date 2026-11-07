#!/usr/bin/env python3
"""Read-only: dump strings near the render-mode knobs of libWPEWebKit to learn
what each knob controls (Jolla patches are visible in the string neighbourhood)."""
import subprocess, sys

HOST = "root@192.168.2.15"
LIB = "/usr/lib64/libWPEWebKit-2.0.so.1.11.4"
KEYS = ["WEBKIT_WEB_RENDER_DEVICE_FILE", "WEBKIT_SKIA_ENABLE_CPU_RENDERING",
        "WEBKIT_USE_SKIA_FOR_COMPOSITION", "WPE_GL_FENCE_DISABLED",
        "WEBKIT_EGL_PIXEL_LAYOUT", "WEBKIT_TILE_ALLOC_SYNC"]

def run(cmd):
    p = subprocess.run(["sshpass", "-e", "ssh", "-o", "StrictHostKeyChecking=no",
                        "-o", "ConnectTimeout=8", HOST, cmd],
                       capture_output=True, text=True, env={"SSHPASS": "sailfish", "PATH": "/usr/bin:/bin"})
    return p.stdout

def main():
    out = run(f"strings -a -t d {LIB}")
    lines = [l for l in out.splitlines() if l.strip()]
    # strings -t d gives "<offset> <str>"
    idx = {}
    for i, l in enumerate(lines):
        idx[l.split(None, 1)[-1]] = i
    print(f"== total strings: {len(lines)}")
    for k in KEYS:
        i = idx.get(k)
        if i is None:
            print(f"\n### {k}: NOT FOUND")
            continue
        print(f"\n### {k}  @offset {lines[i].split()[0]}")
        for j in range(max(0, i - 6), min(len(lines), i + 7)):
            mark = ">>" if j == i else "  "
            print(f"{mark} {lines[j][:160]}")
    print("\n== any string mentioning render_device / headless / offscreen device")
    for l in lines:
        s = l.split(None, 1)[-1]
        if any(t in s.lower() for t in ("render_device", "headless", "device_file", "pixel_readback")):
            print("  ", l[:180])

main()
