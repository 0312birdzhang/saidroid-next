#!/bin/bash
# Pixel-level functional parity for the direct-copy path, run in the VM (needs PIL).
#   scripts/perf/functional-probe.sh <out.json>
cd /media/psf/Home/WorkSpace/saidroid-next
OUT=${1:-build/evidence/r79/functional.json}
python3 - "$OUT" <<'PY'
import json, sys
from pathlib import Path
from PIL import Image, ImageChops
TOL = 8
def compare(a, b):
    ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    if ia.size != ib.size:
        return dict(size_a=ia.size, size_b=ib.size, comparable=False)
    diff = ImageChops.difference(ia, ib)
    hist = diff.histogram()
    total = ia.size[0] * ia.size[1] * 3
    over = sum(sum(hist[c * 256 + TOL + 1:c * 256 + 256]) for c in range(3))
    bbox = diff.getbbox()
    bands = {}
    w, h = ia.size
    for name, img in (('legacy', ia), ('copy', ib)):
        bands[name] = [img.getpixel((int(w * f), h // 2)) for f in (0.1, 0.3, 0.5, 0.7, 0.9)]
    return dict(size_a=ia.size, comparable=True,
                channels_over_tolerance=round(100.0 * over / total, 4),
                mean_abs_channel_diff=round(
                    sum(v * hist[c * 256 + v] for c in range(3) for v in range(256)) / total, 5),
                identical=bbox is None, diff_bbox=bbox, bands=bands)
result = {}
for name, a, b in (
        ('qq_login', 'build/perf/qq-r78/screen.png', 'build/perf/qq-copy-r79/screen.png'),
        ('colour_bands', 'build/perf/scroll-color-legacy-r79/screen.png',
         'build/perf/scroll-color-copy-r79/screen.png')):
    result[name] = compare(a, b)
Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)
Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
PY
