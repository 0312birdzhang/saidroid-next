#!/usr/bin/env python3
"""Require webpage content below QQ's native title bar, rejecting blank H5 frames."""
import argparse,json
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('image');a=p.parse_args()
im=Image.open(a.image).convert('RGB');w,h=im.size
# QQ's native header occupies y<200. Text-only titles/loading stripes cannot pass.
blue=dark=rows=0;total=0
for y in range(250,h-80,3):
 row=0
 for x in range(40,w-40,3):
  r,g,b=im.getpixel((x,y));total+=1
  if b>150 and g>95 and r<90 and b-r>80:blue+=1;row+=1
  if max(r,g,b)<150:dark+=1;row+=1
 if row>8:rows+=1
result={'result':'QQ_WEBVIEW_PIXELS=ready' if blue/total>.04 and dark/total>.001 and rows>=max(20,h//55) else 'QQ_WEBVIEW_PIXELS=blank-or-incomplete','blue_fraction':blue/total,'dark_fraction':dark/total,'content_rows':rows,'size':[w,h]}
print(json.dumps(result,indent=2))
assert result['result']=='QQ_WEBVIEW_PIXELS=ready',result
