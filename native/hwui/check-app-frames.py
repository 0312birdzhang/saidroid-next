#!/usr/bin/env python3
"""Reject an empty/black GPU scene before any tap can repair a missing frame."""
from pathlib import Path
import argparse,json
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('prefix',type=Path);a=p.parse_args()
results=[]
for name in ['before','settled','resume1','resume2']:
 path=a.prefix.parent/(a.prefix.name+'-'+name+'.png');im=Image.open(path).convert('RGB');assert im.size==(1080,2160)
 pixels=list(im.resize((108,216)).getdata());green=sum(g>110 and g>r*1.6 and g>b*.7 for r,g,b in pixels)/len(pixels);black=sum(max(c)<8 for c in pixels)/len(pixels)
 result=dict(frame=name,green_fraction=round(green,5),black_fraction=round(black,5));results.append(result)
 assert green>.12 and black<.5,(str(path),result)
print(json.dumps(dict(result='HWUI_STATIC_SCENES=ready',frames=results),indent=2))
