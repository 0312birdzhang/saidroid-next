#!/usr/bin/env python3
"""Extract named entries from Google's CTS ZIP through bounded HTTP ranges.
Retains inventory and hashes; never downloads the multi-GB complete archive.
"""
import argparse,hashlib,io,json,struct,urllib.request,zipfile,zlib,time,concurrent.futures
from pathlib import Path
BASE='https://dl.google.com/dl/android/cts/'
def get_once(url,start,end):
    req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}'})
    with urllib.request.urlopen(req,timeout=40)as r:
        if r.status!=206:raise RuntimeError('Server did not honor bounded range request')
        data=r.read(end-start+2)
        if len(data)!=end-start+1:raise RuntimeError('Incomplete range')
        return data

def get(url,start,end):
    for attempt in range(3):
        try:return get_once(url,start,end)
        except (OSError,RuntimeError):
            if attempt==2:raise
            time.sleep(1)

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',default='android-cts-10_r16-linux_x86-arm.zip');p.add_argument('--out',type=Path,required=True);p.add_argument('--all-configs',action='store_true');p.add_argument('entries',nargs='*');a=p.parse_args()
    if a.archive not in ['android-cts-10_r16-linux_x86-arm.zip','android-cts-verifier-10_r16-linux_x86-arm.zip']:p.error('Pinned official API29 archives only')
    u=BASE+a.archive
    with urllib.request.urlopen(urllib.request.Request(u,headers={'Range':'bytes=-65536'}),timeout=40)as r:
        if r.status!=206:raise RuntimeError('Range unsupported')
        total=int(r.headers['Content-Range'].split('/')[-1]);tail=r.read(65537)
    e=tail.rfind(b'PK\x05\x06');_,disk,cdisk,n,nt,sz,off,comment=struct.unpack_from('<4s4H2IH',tail,e)
    if disk or cdisk or n!=nt or nt==65535:raise RuntimeError('Unsupported ZIP layout')
    central=get(u,off,off+sz-1)
    # A synthetic ZIP with central-directory offsets unchanged is safe because
    # ZipInfo.header_offset is only used to issue independent bounded requests.
    end=struct.pack('<4s4H2IH',b'PK\x05\x06',0,0,nt,nt,sz,0,0)
    infos=zipfile.ZipFile(io.BytesIO(central+end)).infolist()
    a.out.mkdir(parents=True,exist_ok=True)
    inventory={'url':u,'archive_bytes':total,'entries':[dict(path=i.filename,bytes=i.file_size,compressed_bytes=i.compress_size,crc32=f'{i.CRC:08x}')for i in infos]}
    (a.out/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    byname={i.filename:i for i in infos};results=[]
    # Central-directory header offsets remain the original remote offsets.
    adjustment=0
    def extract(name):
        info=byname[name];offset=info.header_offset+adjustment
        header=get(u,offset,offset+29);fields=struct.unpack('<4s5H3I2H',header);assert fields[0]==b'PK\x03\x04'
        length,extra=fields[-2:];start=offset+30+length+extra
        if info.file_size>200*1024*1024:raise RuntimeError('Individual entry too large')
        raw=get(u,start,start+info.compress_size-1)
        data=zlib.decompress(raw,-15)if info.compress_type==8 else raw
        assert len(data)==info.file_size and zlib.crc32(data)==info.CRC
        target=a.out/Path(name).name;target.write_bytes(data)
        return dict(entry=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    entries=[i.filename for i in infos if i.filename.endswith('.config')]if a.all_configs else a.entries
    with concurrent.futures.ThreadPoolExecutor(max_workers=8 if a.all_configs else 1)as pool:results=list(pool.map(extract,entries))
    (a.out/'extracted.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'archive':a.archive,'archive_bytes':total,'inventory_entries':len(infos),'extracted':results}))
if __name__=='__main__':main()
