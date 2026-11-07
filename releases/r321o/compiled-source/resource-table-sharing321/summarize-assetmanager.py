from pathlib import Path
import json,re,hashlib,statistics
p=Path(__file__).parent;out=p/'assetmanager-vm-v2';result=json.loads((out/'result.json').read_text());assert result['passed'];keys=['Size','Rss','Pss','Shared_Clean','Shared_Dirty','Private_Clean','Private_Dirty','Anonymous','Swap','SwapPss'];rows=[]
def parse(f):
 maps=[]
 for line in f.read_text().splitlines():
  m=re.match(r'^([0-9a-f]+)-([0-9a-f]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(.*)$',line)
  if m:
   row=dict(start=int(m[1],16),end=int(m[2],16),permissions=m[3],offset=int(m[4],16),path=m[7],values={});maps.append(row)
  elif maps and ':'in line:
   k,v=line.split(':',1)
   if k in keys:maps[-1]['values'][k]=int(v.split()[0])
 return maps
for item in result['rows']:
 d=out/item['label'];before=parse(d/(item['process']+'-before.smaps'));after=parse(d/(item['process']+'-after.smaps'));total=lambda maps:{k:sum(row['values'].get(k,0)for row in maps)for k in keys};b=total(before);a=total(after);anon=[row for row in after if row['permissions'].startswith('rw')and row['path']==''and 30000<row['values'].get('Size',0)<32000];resource=[row for row in after if row['path'].endswith('framework-res.apk')];rows.append(dict(label=item['label'],process=item['process'],before_kib=b,after_kib=a,delta_kib={k:a[k]-b[k]for k in keys},anonymous_resource_sized_maps=anon,apk_maps=resource,apk_totals_kib=total(resource),values_sha256=item['values_sha256']))
for row in rows:
 if row['label']=='compressed':assert len(row['anonymous_resource_sized_maps'])==1
 else:assert not row['anonymous_resource_sized_maps'];assert any(r['offset']==12726272 and r['permissions']=='r--s'and r['values'].get('Anonymous')==0 for r in row['apk_maps'])
groups={label:{k:statistics.mean(row['delta_kib'][k]for row in rows if row['label']==label)for k in keys}for label in ['compressed','stored']};decrease={k:groups['compressed'][k]-groups['stored'][k]for k in keys};assert decrease['Anonymous']>29000 and decrease['Private_Dirty']>29000 and decrease['Pss']>0
report=dict(passed=True,scope='Causal actual-AssetManager VM comparison; two concurrent ordinary L processes per archive encoding, identical decoded string/color/dimension/XML values and policy',rows=rows,mean_delta_kib=groups,mean_reduction_kib=decrease,resource_table_bytes=31447228,stored_resource_file_offset=12726272,both_variants_values_sha256=rows[0]['values_sha256'],limitations=['Normal Resources APIs touch only required file-backed resource pages; this is not a full-page fault benchmark.','Per-process VM savings do not establish total phone residency or explain the prior compositor restart.','Anonymous shared/JIT/native allocations outside the resource table remain unchanged.'],device_accessed=False)
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,mean_delta_kib=groups,mean_reduction_kib=decrease),indent=2))
