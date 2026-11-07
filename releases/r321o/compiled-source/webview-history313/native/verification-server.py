#!/usr/bin/env python3
"""Loopback-only verification flow with no accounts or outside requests."""
import http.server,json,sys
from pathlib import Path
log=Path(sys.argv[1])
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  with log.open('a')as out:out.write(json.dumps(dict(path=self.path,cookies=self.headers.get('Cookie',''),test_header=self.headers.get('X-SD-Test','')))+'\n')
  if self.path=='/redirect':self.send_response(302);self.send_header('Location','/next');self.end_headers();return
  self.send_response(200);self.send_header('Content-Type','text/html; charset=UTF-8');self.send_header('Set-Cookie','fromServer=three; HttpOnly; Path=/');self.end_headers()
  if self.path=='/start':
   page="""<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><body style="margin:0;background:#fafafa;font:22px sans-serif"><h2>Verification bridge</h2><div id="result">Ready</div><button style="display:block;width:100vw;height:50vh;font-size:24px;background:#1378be;color:white" onclick="document.getElementById('result').textContent=Bridge.echo('touch')+'|'+prompt('roundtrip','test');location.href='testbridge://next'">Continue verification</button>"""
  else:page='<!doctype html><meta name="viewport" content="width=device-width"><body style="margin:0;background:#00aa55;color:white;font:26px sans-serif"><h1>Verification complete</h1><p>Native callback and redirect handled</p></body>'
  self.wfile.write(page.encode())
http.server.HTTPServer(('127.0.0.1',18786),Handler).serve_forever()
