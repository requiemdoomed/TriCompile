import json
import sys
import unittest
import urllib.request
import urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import compile_source,Machine,CompileError,encode,decode
from runners import run_native,capabilities
import server

class CompilerTests(unittest.TestCase):
    def test_loop(self):
        self.assertEqual(Machine(compile_source('set x to 1\nwhile x <= 3\nshow x\nset x to x + 1\nend')).run(),'1\n2\n3')
    def test_branches(self):
        for value,expected in [(1,'yes'),(0,'no')]:
            self.assertEqual(Machine(compile_source(f'if {value}\nshow "yes"\nelse\nshow "no"\nend')).run(),expected)
    def test_highlevel(self):
        self.assertEqual(Machine(compile_source('let x = 7 * 6;\nprint(x);','highlevel')).run(),'42')
    def test_nested(self):
        self.assertEqual(Machine(compile_source('set x to 0\nwhile x < 2\nif x == 1\nshow "one"\nend\nset x to x + 1\nend')).run(),'one')
    def test_assembly_roundtrip(self):
        code=compile_source('PUSH 8\nPUSH 2\nDIV\nPRINT\nHALT','assembly')
        self.assertEqual(Machine(decode(encode(code))).run(),'4')
    def test_step(self):
        vm=Machine(compile_source('set x to 5\nshow x'));vm.step();self.assertEqual(vm.stack,[5]);vm.step();self.assertEqual(vm.variables,{'x':5})
    def test_errors(self):
        for source,mode in [('end','beginner'),('if 1','beginner'),('show f()','beginner'),('PUSH null','assembly'),('JMP -1','assembly'),('ADD 2','assembly')]:
            with self.subTest(source=source),self.assertRaises(CompileError): compile_source(source,mode)
    def test_runtime_errors(self):
        for source in ['show missing','show 1 // 0','while 1\nshow 1\nend']:
            with self.subTest(source=source),self.assertRaises(CompileError): Machine(compile_source(source)).run()
    def test_bad_bytecode(self):
        with self.assertRaises(CompileError): decode(b'bad')

class NativeTests(unittest.TestCase):
    def test_real_programs(self):
        sources={'python':'print(int(input()) * 2)','javascript':'console.log(Number(require("fs").readFileSync(0,"utf8"))*2)','c':'#include <stdio.h>\nint main(void){int n;scanf("%d",&n);printf("%d\\n",n*2);return 0;}','cpp':'#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2<<"\\n";}'}
        for lang,source in sources.items():
            with self.subTest(language=lang):
                if not capabilities()[lang]: self.skipTest(lang+' not installed')
                result=run_native(lang,source,'21\n');self.assertEqual(result['exit_code'],0,result);self.assertEqual(result['stdout'].strip(),'42')
    def test_compile_errors(self):
        for lang in ('python','javascript','c','cpp'):
            if capabilities()[lang]:
                with self.subTest(language=lang): self.assertNotEqual(run_native(lang,'this is not valid !!!',compile_only=True)['exit_code'],0)
    def test_timeout(self):
        self.assertTrue(run_native('python','while True: pass')['timed_out'])

class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=server.start(False)
    @classmethod
    def tearDownClass(cls): cls.app.shutdown();cls.app.server_close()
    def test_page(self):
        page=urllib.request.urlopen('http://127.0.0.1:8765').read().decode();self.assertIn(server.TOKEN,page);self.assertIn('TriCompile',page)
    def test_api(self):
        body=json.dumps({'mode':'beginner','source':'show 42','action':'run'}).encode()
        request=urllib.request.Request('http://127.0.0.1:8765/api/execute',data=body,headers={'X-TriCompile-Token':server.TOKEN})
        self.assertEqual(json.load(urllib.request.urlopen(request))['output'],'42')
    def test_unauthorized(self):
        with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765/api/execute',data=b'{}'))
        self.assertEqual(error.exception.code,403)

if __name__=='__main__': unittest.main()
