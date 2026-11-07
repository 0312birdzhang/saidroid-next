import subprocess, sys
COMPS = ["/var/tmp/saidroid-next-api29-component-20261026-r63",
         "/var/tmp/saidroid-next-api29-component-r64",
         "/var/tmp/saidroid-next-api29-component-diag2"]
MARKS = ["SAILDROID_NO_FASTPATH","SAILDROID_COMPOSE_ON_VSYNC","SAILDROID_PERF","layer_full","cfall","creq",
         "perf_commits_since_vsync","frame_callback_gap","composes","presents","SDWINDOW_SESSION"]
for c in COMPS:
    p = c + "/root/lib/libsdwindow.so"
    print("=== " + c)
    try:
        out = subprocess.run(["strings", p], capture_output=True, text=True).stdout
    except FileNotFoundError:
        print("MISSING"); continue
    print("so_bytes=%d" % len(open(p,'rb').read()))
    for m in MARKS:
        print("  %-26s %d" % (m, out.count(m)))
    sys.stdout.flush()
