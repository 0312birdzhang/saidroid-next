#!/usr/bin/env python3
"""Check actual webpage pixels and scroll displacement, not just file existence."""
from pathlib import Path
import argparse,json
from PIL import Image,ImageChops
p=argparse.ArgumentParser();p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--log',type=Path);a=p.parse_args()
images=[Image.open(x).convert('RGB') for x in [a.before,a.after]]
assert images[0].size==images[1].size
w,h=images[0].size
colors={'blue':(11,61,145),'brown':(181,101,29),'green':(0,170,85)}
def band(image,color):
    rows=[];total=0
    for y in range(h):
        count=sum(max(abs(v-t) for v,t in zip(image.getpixel((x,y)),color))<=8 for x in range(w//4,3*w//4,4))
        if count>=(w//8)*0.65:rows.append(y)
        total+=count
    return {'first':min(rows) if rows else None,'last':max(rows) if rows else None,'samples':total}
stats=[{key:band(image,color) for key,color in colors.items()} for image in images]
assert all(item['brown']['samples']>w*h/60 for item in stats),stats
assert stats[0]['blue']['samples']>w*h/60,stats
assert stats[1]['green']['samples']>w*h/60,stats
before=stats[0]['brown']['first'];after=stats[1]['brown']['first']
assert before is not None and after is not None and before-after>=h*0.15,(before,after)
assert ImageChops.difference(*images).getbbox() is not None
if a.log:
    log=a.log.read_text(errors='replace')
    assert 'JS=42' in log and 'scrollY=' in log
record={'result':'WEBVIEW_PIXELS=ready','size':[w,h],'brown_boundary_up_px':before-after,'bands':stats}
print(json.dumps(record,indent=2))
