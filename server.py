"""TriCompile loopback server. Author: Swayam Shakya."""
import base64
import json
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from core import compile_source,encode,decode,Machine
from runners import capabilities,run_native
TOKEN=secrets.token_urlsafe(32)
ROOT=Path(__file__).parent
class Handler(BaseHTTPRequestHandler):
    def send(self,status,data,kind='application/json'):
        body=json.dumps(data).encode() if kind=='application/json' else data
        self.send_response(status); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.headers.get('Host') not in ('127.0.0.1:8765','localhost:8765'): return self.send(403,{'error':'Invalid host'})
        if self.path in ('/','/index.html'):
            return self.send(200,(ROOT/'index.html').read_bytes().replace(b'__TOKEN__',TOKEN.encode()),'text/html; charset=utf-8')
        if self.path=='/api/capabilities': return self.send(200,capabilities())
        self.send(404,{'error':'Not found'})
    def do_POST(self):
        if self.headers.get('X-TriCompile-Token')!=TOKEN: return self.send(403,{'error':'Open the interface from the local server'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=200000: raise ValueError('Request limit: 200 KB')
            data=json.loads(self.rfile.read(length)); mode=data.get('mode','beginner'); source=data.get('source',''); action=data.get('action','run')
            if not isinstance(source,str) or len(source)>50000: raise ValueError('Source limit: 50000 characters')
            if action not in ('run','compile','step'): raise ValueError('Unknown action')
            if mode in ('python','javascript','c','cpp'):
                if action=='step': raise ValueError('Instruction stepping is available for educational modes')
                result=run_native(mode,source,data.get('stdin',''),action=='compile')
            else:
                code=decode(bytes.fromhex(source)) if mode=='bytecode' else compile_source(source,mode)
                result={'code':code,'hex':encode(code).hex(),'binary':' '.join(f'{b:08b}' for b in encode(code))}
                if action!='compile':
                    machine=Machine(code)
                    if action=='run': machine.run()
                    else:
                        count=data.get('steps',1)
                        if type(count)!=int or not 1<=count<=10000: raise ValueError('Invalid step count')
                        for _ in range(count):
                            if machine.halted: break
                            machine.step()
                    result.update(machine.state())
            self.send(200,result)
        except (ValueError,TypeError,OverflowError,RecursionError) as e: self.send(400,{'error':str(e)})
    def log_message(self,*args): pass

def start(open_browser=True):
    server=ThreadingHTTPServer(('127.0.0.1',8765),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    print('TriCompile: http://127.0.0.1:8765')
    if open_browser: webbrowser.open('http://127.0.0.1:8765')
    return server
if __name__=='__main__':
    app=start()
    try: threading.Event().wait()
    except KeyboardInterrupt: app.shutdown(); app.server_close()
