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
queue=bytearray();header=None;size=None;events=[];stats=[];ready=False;loaded=None;requested=0;cpu_start=None
start=time.monotonic();deadline=start+25
try:
 while time.monotonic()<deadline:
  now=time.monotonic()
  if loaded and requested<1 and now-loaded>3:
   send({'op':'eval','id':1,'script':"JSON.stringify({title:document.title,ready:document.readyState,text:document.body.innerText,html:document.documentElement.outerHTML.slice(0,12000),height:document.body.scrollHeight})"});requested+=1
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
    send({'op':'load','url':'https://accounts.qq.com/helpcenter/index?_wv=3&_wwv=128'})
   elif kind=='frame':
    assert len(pixels)==720*1280*4;(root/'last.rgba').write_bytes(pixels);send({'op':'frame_ack','seq':event['seq']})
   elif kind=='load' and event['status']==2:loaded=time.monotonic()
   elif kind=='eval':
    print(json.dumps(event,ensure_ascii=False),flush=True);(root/'dom.json').write_text(json.dumps(event,ensure_ascii=False,indent=2));deadline=time.monotonic()+1
   elif kind=='stats':
    st=Path('/proc/%d/stat'%p.pid).read_text().split(') ',1)[1].split();event['cpu_ticks']=int(st[11])+int(st[12]);event['process_group_ticks']=process_ticks();stats.append(event)
    if len(stats)==2:break
  if len(stats)==2:break
 print('NETWORK_PROBE_EVENTS='+json.dumps(events,ensure_ascii=False),flush=True)

finally:
 try:send({'op':'quit'});p.wait(timeout=3)
 except (OSError,subprocess.TimeoutExpired):pass
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 log.close();subprocess.run(['mcetool','--blank-screen'],check=True)
