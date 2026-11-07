"""Run the real host IPC with display off; quantify idle frame/CPU work."""
import os,sys,json,time,struct,subprocess,pwd,signal,select
from pathlib import Path
release,label=sys.argv[1:3]
account=pwd.getpwnam('defaultuser');root=Path('/home/defaultuser/.local/share/saidroid-webview-probes')/label
root.mkdir(parents=True,exist_ok=False);os.chown(root,account.pw_uid,account.pw_gid)
env={'PATH':'/usr/bin:/bin','HOME':str(root),'XDG_DATA_HOME':str(root/'data'),'XDG_CACHE_HOME':str(root/'cache'),'XDG_CONFIG_HOME':str(root/'config'),'XDG_RUNTIME_DIR':'/run/user/100000','WAYLAND_DISPLAY':'../../display/wayland-0','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/100000/dbus/user_bus_socket'}
subprocess.run(['mcetool','--blank-screen'],check=True)
log=(root/'host.log').open('wb')
p=subprocess.Popen([release+'/libexec/sdwebview-host','720','1280'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,env=env,user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid),start_new_session=True)
def process_ticks():
 result={}
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   pid=int(proc.name)
   if os.getpgid(pid)!=p.pid:continue
   st=(proc/'stat').read_text().split(') ',1)[1].split();result[proc.name]=int(st[11])+int(st[12])
  except OSError:pass
 return result
def send(o):
 b=json.dumps(o).encode();p.stdin.write(struct.pack('>I',len(b))+b);p.stdin.flush()
queue=bytearray();header=None;size=None;events=[];stats=[];ready=False;loaded=None;requested=0;cpu_start=None;hidden_at=None;shown_at=None;resumed_frames=0
start=time.monotonic();deadline=start+18
try:
 while time.monotonic()<deadline:
  now=time.monotonic()
  if loaded and hidden_at is None and now-loaded>2:
   send({'op':'visibility','active':False});hidden_at=now
  if hidden_at and requested<2 and now-hidden_at>1+requested*3:
   send({'op':'stats'});requested+=1
  if len(stats)==2 and shown_at is None:
   send({'op':'visibility','active':True});shown_at=now
  if shown_at and now-shown_at>2:break
  if not select.select([p.stdout],[],[],.05)[0]:continue
  chunk=os.read(p.stdout.fileno(),65536)
  if not chunk:break
  queue.extend(chunk)
  while True:
   if header is None:
    if len(queue)<4:break
    n=struct.unpack('>I',queue[:4])[0];assert 0<n<1024*1024
    if len(queue)<4+n:break
    header=json.loads(queue[4:4+n]);del queue[:4+n]
    size=header.get('bytes',0);assert 0<=size<=9*1024*1024
   if len(queue)<size:break
   pixels=bytes(queue[:size]);del queue[:size]
   event=header;header=None;kind=event['event'];events.append(event)
   if kind=='ready':
    send({'op':'settings','javascript':True,'images':True,'storage':False})
    send({'op':'load','html':"<!doctype html><body style='background:#0b3d91;color:white;font-size:50px'><b id='n'>0</b><script>var count=0;function tick(){document.getElementById('n').textContent=++count;requestAnimationFrame(tick)};requestAnimationFrame(tick)</script>",'base':'https://saidroid.invalid/'})
   elif kind=='frame':
    assert len(pixels)==720*1280*4
    if shown_at:resumed_frames+=1
    send({'op':'frame_ack','seq':event['seq']})
   elif kind=='load' and event['status']==2:loaded=time.monotonic()
   elif kind=='stats':
    st=Path('/proc/%d/stat'%p.pid).read_text().split(') ',1)[1].split();event['cpu_ticks']=int(st[11])+int(st[12]);event['process_group_ticks']=process_ticks();stats.append(event)
    if len(stats)>2:break
  if len(stats)>2:break
 assert len(stats)==2,events
 frames=stats[1]['frames']-stats[0]['frames'];renders=stats[1]['renders']-stats[0]['renders']
 span=stats[1]['elapsed_ms']-stats[0]['elapsed_ms'];cpu_ms=(stats[1]['cpu_ticks']-stats[0]['cpu_ticks'])*1000/os.sysconf('SC_CLK_TCK')
 group_ms=sum(max(0,value-stats[0]['process_group_ticks'].get(pid,value)) for pid,value in stats[1]['process_group_ticks'].items())*1000/os.sysconf('SC_CLK_TCK')
 result={'group_cpu_ms':group_ms,'group_single_core_cpu_percent':100*group_ms/span,'resumed_frames':resumed_frames,'result':'WEBVIEW_VISIBILITY=ready' if frames==0 and renders==0 and resumed_frames>=2 else 'WEBVIEW_VISIBILITY=failed','frames_delta':frames,'renders_delta':renders,'span_ms':span,'host_cpu_ms':cpu_ms,'host_single_core_cpu_percent':100*cpu_ms/span,'stats':stats}
 print(json.dumps(result,indent=2),flush=True)
 (root/'result.json').write_text(json.dumps(result,indent=2))
 assert frames==0 and renders==0 and resumed_frames>=2,result
finally:
 try:send({'op':'quit'});p.wait(timeout=3)
 except (OSError,subprocess.TimeoutExpired):pass
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 log.close();subprocess.run(['mcetool','--blank-screen'],check=True)
