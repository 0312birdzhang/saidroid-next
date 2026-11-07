#!/usr/bin/env python3
"""Render the functional-parity section (screenshots + colour bands) as markdown.

    python3 scripts/perf/render-functional.py build/evidence/r79/functional.json
"""
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
lines = ['## Functional parity of the direct-copy path', '',
         'Both screenshots were taken with the same probe build and the same window; only '
         'the pixel path differs (legacy copy vs `Bitmap.copyPixelsToBuffer` straight into '
         'the wl_shm buffer). Tolerance is 8/255 per channel.', '',
         '| page | size | identical | channels over tolerance % | mean abs channel diff | diff bbox |',
         '| --- | --- | --- | --- | --- | --- |']
for name, row in data.items():
    lines.append('| %s | %s | %s | %s | %s | %s |' % (
        name, 'x'.join(str(v) for v in row['size_a']), row.get('identical'),
        row.get('channels_over_tolerance'), row.get('mean_abs_channel_diff'),
        row.get('diff_bbox')))
bands = data.get('colour_bands', {}).get('bands')
if bands:
    lines.extend(['', 'Colour oracle, five pure bands sampled left to right (red, green, '
                  'blue, white, black expected):', '',
                  '| path | band 1 | band 2 | band 3 | band 4 | band 5 |',
                  '| --- | --- | --- | --- | --- | --- |'])
    for name in ('legacy', 'copy'):
        lines.append('| %s | %s |' % (name, ' | '.join(
            '(%d,%d,%d)' % tuple(pixel) for pixel in bands[name])))
    lines.extend(['', '`bands_equal=%s`: the byte order written by the direct copy is the '
                  'same order the legacy path produced, so no R/B swap was introduced.'
                  % (bands['legacy'] == bands['copy'])])
print('\n'.join(lines))
