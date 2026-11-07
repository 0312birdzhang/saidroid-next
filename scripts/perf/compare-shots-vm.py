#!/usr/bin/env python3
"""Compare two phone screenshots pixel by pixel (P5 gate control, VM side).

    python3 scripts/perf/compare-shots-vm.py a.png b.png

Prints the size, how many pixels differ, the mean absolute channel difference and
the bounding box of the differing area. Animated widgets on a live page legitimately
differ between two captures; the numbers say how much, instead of a bare "equal".
"""
import sys
from PIL import Image, ImageChops

TOLERANCE = 8


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    a = Image.open(sys.argv[1]).convert('RGB')
    b = Image.open(sys.argv[2]).convert('RGB')
    print('size_a', a.size, 'size_b', b.size)
    if a.size != b.size:
        raise SystemExit('different sizes; not comparable')
    diff = ImageChops.difference(a, b)
    histogram = diff.histogram()
    total = a.size[0] * a.size[1] * 3
    differing = sum(count for index, count in enumerate(histogram) if index % 256 > TOLERANCE)
    mean = sum(index % 256 * count for index, count in enumerate(histogram)) / total
    bbox = diff.getbbox()
    print('identical', bbox is None)
    print('channels_over_tolerance_%%', round(100.0 * differing / total, 4))
    print('mean_abs_channel_diff', round(mean, 4))
    print('diff_bbox', bbox)


if __name__ == '__main__':
    main()
