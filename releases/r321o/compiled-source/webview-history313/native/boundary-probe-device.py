from pathlib import Path
import os,sys,re,pwd,subprocess,time,json,struct,threading,queue,signal,http.server,base64,hashlib
label=sys.argv[1];release=sys.argv[2]
assert re.fullmatch('[a-z0-9-]+',label) and re.fullmatch('api29-[a-z0-9-]+',release)
user=pwd.getpwnam('defaultuser');base=Path('/home/art/test')/label;base.mkdir(exist_ok=False);os.chown(base,user.pw_uid,user.pw_gid)
def compositor_health():
 e=dict(os.environ,XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0')
 subprocess.run(['/home/art/test/hwui-tools/sd-wayland-health'],env=e,user=user.pw_uid,group=user.pw_gid,extra_groups=os.getgrouplist(user.pw_name,user.pw_gid),check=True,timeout=5)
compositor_health()
requests=[]
class Server(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  requests.append(dict(method='GET',path=self.path,cookie=self.headers.get('Cookie',''),header=self.headers.get('X-SD-Test','')))
  if self.path=='/redirect':self.send_response(302);self.send_header('Location','/next');self.end_headers();return
  self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Set-Cookie','fromServer=two; Path=/; HttpOnly');self.end_headers()
  self.wfile.write(("<!doctype html><meta name='viewport' content='width=device-width'><body style='margin:0;background:#0b3d91;color:white'><div id='result'>"+self.path+"</div><script>document.title='NATIVE-PAGE';</script>").encode())
 def do_POST(self):
  body=self.rfile.read(int(self.headers.get('Content-Length','0'))).decode();requests.append(dict(method='POST',path=self.path,body=body))
  self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<body style="background:#00aa55">POST received</body>')
server=http.server.HTTPServer(('127.0.0.1',0),Server);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port)
env=dict(os.environ,HOME=str(base),XDG_DATA_HOME=str(base/'data'),XDG_CACHE_HOME=str(base/'cache'),XDG_CONFIG_HOME=str(base/'config'),XDG_RUNTIME_DIR='/run/user/100000',WAYLAND_DISPLAY='../../display/wayland-0',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/100000/dbus/user_bus_socket')
for key in ['LD_PRELOAD','LD_LIBRARY_PATH','BIONIC_TRANSLATION_CONFIG_DIR']:env.pop(key,None)
kw=dict(user=user.pw_uid,group=user.pw_gid,extra_groups=os.getgrouplist(user.pw_name,user.pw_gid))
log=open(base/'host.log','wb');process=subprocess.Popen([str(Path('/home/art/releases')/release/'libexec/sdwebview-host'),'720','1280'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,start_new_session=True,**kw)
events=queue.Queue();seen=[];frames=0;seq=0
lock=threading.Lock()
def send(**packet):
 b=json.dumps(packet).encode()
 with lock:process.stdin.write(struct.pack('>I',len(b))+b);process.stdin.flush()
def exact(n):
 b=b''
 while len(b)<n:
  part=process.stdout.read(n-len(b))
  if not part:raise EOFError()
  b+=part
 return b
def reader():
 global frames
 try:
  while True:
   event=json.loads(exact(struct.unpack('>I',exact(4))[0]));seen.append(event)
   if event['event']=='frame':
    pixels=exact(event['bytes']);frames+=1;send(op='frame_ack',seq=event['seq'])
   elif event['event']=='navigation':
    send(op='navigation_reply',id=event['id'],handled=event['url'].startswith('testbridge:'),newWindow=event.get('newWindow',False),url=event['url'])
   elif event['event']=='js_interface':
    request=event['request'];assert request['name']=='Bridge' and request['method']=='echo'
    send(op='js_interface_reply',id=event['id'],confirmed=True,text=json.dumps(dict(ok=True,value='native:'+request['args'][0],undefined=False)))
   elif event['event']=='js_dialog':send(op='js_dialog_reply',id=event['id'],confirmed=True,text='prompt-ok')
   events.put(event)
 except Exception as e:events.put(dict(event='reader_failure',type=type(e).__name__))
threading.Thread(target=reader,daemon=True).start()
def wait(predicate,seconds=15):
 deadline=time.monotonic()+seconds
 while time.monotonic()<deadline:
  for e in seen:
   if predicate(e):return e
  if process.poll() is not None:raise RuntimeError('host exit '+str(process.returncode))
  time.sleep(.03)
 raise TimeoutError([e for e in seen if e['event'] not in ['frame','cookies']][-15:])
def evaluate(script):
 global seq
 seq+=1;id=seq;send(op='eval',id=id,script=script);return wait(lambda e:e['event']=='eval' and e['id']==id)['result']
try:
 wait(lambda e:e['event']=='ready')
 send(op='settings',javascript=True,images=True,storage=True,deviceScale=2.625,javascriptWindows=True)
 send(op='interfaces',interfaces={'Bridge':['echo']})
 send(op='cookies_sync',version=1,entries=[dict(name='fromAndroid',value='one',domain='127.0.0.1',path='/',secure=False,httpOnly=False,expires=0,session=True)])
 send(op='load',url=origin+'/start',headers={'X-SD-Test':'header'})
 wait(lambda e:e['event']=='load' and e.get('status')==2)
 assert any(r.get('cookie','').find('fromAndroid=one')>=0 and r.get('header')=='header' for r in requests),requests
 wait(lambda e:e['event']=='cookies' and any(c['name']=='fromServer' for c in e['entries']))
 assert json.loads(evaluate("Bridge.echo('hello')"))=='native:hello'
 assert json.loads(evaluate("prompt('ordinary','initial')"))=='prompt-ok'
 evaluate("location.href='testbridge://handled';true")
 wait(lambda e:e['event']=='navigation' and e['url'].startswith('testbridge:'))
 evaluate("location.href='/redirect';true")
 wait(lambda e:e['event']=='load' and e.get('status')==2 and e.get('url','').endswith('/next'))
 evaluate("window.open('/popup','_blank');true")
 wait(lambda e:e['event']=='load' and e.get('status')==2 and e.get('url','').endswith('/popup'))
 send(op='post',url=origin+'/post',body=base64.b64encode(b'name=hello+world&number=42').decode())
 deadline=time.monotonic()+10
 while time.monotonic()<deadline and not any(r['method']=='POST' for r in requests):time.sleep(.05)
 assert any(r.get('body')=='name=hello+world&number=42' for r in requests),requests
 assert frames>0
 print('NATIVE_WEB_BOUNDARY=ready|bridge_return=true|prompt=true|cookie_request_response=true|headers=true|redirect=true|custom_scheme=true|popup=true|post=true|frames='+str(frames))
finally:
 try:send(op='quit');process.wait(timeout=5)
 except Exception:
  if process.poll() is None:os.killpg(process.pid,signal.SIGTERM);process.wait(timeout=5)
 server.shutdown();log.close();compositor_health()
 (base/'result.json').write_text(json.dumps(dict(requests=requests,events=[e for e in seen if e['event'] not in ['frame','cookies']],frames=frames,exit=process.returncode),indent=2)+'\n')
