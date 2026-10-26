"""Local toolchain adapters. Run only your own trusted programs."""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS={'python':sys.executable,'javascript':'node','c':'gcc','cpp':'g++'}
EXT={'python':'.py','javascript':'.js','c':'.c','cpp':'.cpp'}
def capabilities():
    return {k:bool(shutil.which(v)) for k,v in TOOLS.items()}
def execute(command,folder,stdin='',timeout=5):
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc=subprocess.Popen(command,cwd=folder,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=os.name!='nt')
        timed_out=False
        try: proc.communicate(stdin.encode(),timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            if os.name=='nt': subprocess.run(['taskkill','/F','/T','/PID',str(proc.pid)],capture_output=True)
            else: os.killpg(proc.pid,signal.SIGKILL)
            proc.communicate()
        out.seek(0); err.seek(0)
        return {'stdout':out.read(65536).decode(errors='replace'),'stderr':err.read(65536).decode(errors='replace'),'exit_code':proc.returncode,'timed_out':timed_out}
def run_native(language,source,stdin='',compile_only=False):
    if language not in TOOLS: raise ValueError('Unsupported language')
    tool=shutil.which(TOOLS[language])
    if not tool: raise ValueError(f'Install {TOOLS[language]} and add it to PATH; restart TriCompile')
    with tempfile.TemporaryDirectory(prefix='tricompile-') as folder:
        path=Path(folder)/('program'+EXT[language]); path.write_text(source,encoding='utf-8')
        if language in ('c','cpp'):
            binary=str(Path(folder)/('program.exe' if os.name=='nt' else 'program'))
            result=execute([tool,str(path),'-Wall','-Wextra','-std='+('c17' if language=='c' else 'c++17'),'-o',binary],folder,timeout=15)
            if result['exit_code'] or compile_only: return result
            return execute([binary],folder,stdin)
        if compile_only:
            return execute([tool,'-m','py_compile',str(path)] if language=='python' else [tool,'--check',str(path)],folder)
        return execute([tool,str(path)],folder,stdin)
