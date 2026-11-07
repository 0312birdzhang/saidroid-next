#!/usr/bin/env python3
"""Require the real green completion page; callbacks alone cannot pass."""
import json,sys
from PIL import Image
image=Image.open(sys.argv[1]).convert('RGB')
assert image.size==(1080,2160),image.size
pixels=list(image.resize((108,216)).getdata())
green=sum(g>r*1.8 and g>b*1.2 and g>80 for r,g,b in pixels)/len(pixels)
black=sum(max(p)<25 for p in pixels)/len(pixels)
assert green>.75 and black<.05,(green,black)
print(json.dumps(dict(result='WEBVIEW_VERIFICATION_PIXELS=ready',green_fraction=green,black_fraction=black)))
