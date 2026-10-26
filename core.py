"""TriCompile educational compiler and stack machine. Author: Swayam Shakya."""
import ast
import json
import re

OPS = ['PUSH','LOAD','STORE','ADD','SUB','MUL','DIV','MOD','EQ','NE','LT','LE','GT','GE','PRINT','JMP','JZ','HALT']

class CompileError(ValueError):
    pass


def compile_source(source, mode='beginner'):
    code = []
    blocks = []
    def emit(op, arg=None, line=0):
        code.append({'op':op, 'arg':arg, 'line':line})
        return len(code)-1
    def expr(text, line):
        try:
            tree = ast.parse(text, mode='eval').body
        except SyntaxError as e:
            raise CompileError(f'Line {line}, column {e.offset}: invalid expression') from e
        def walk(n):
            if isinstance(n, ast.Constant) and type(n.value) in (int,str,bool): emit('PUSH',n.value,line)
            elif isinstance(n, ast.Name): emit('LOAD',n.id,line)
            elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
                emit('PUSH',0,line); walk(n.operand); emit('SUB',line=line)
            elif isinstance(n, ast.BinOp) and type(n.op) in (ast.Add,ast.Sub,ast.Mult,ast.FloorDiv,ast.Mod):
                walk(n.left); walk(n.right)
                emit({ast.Add:'ADD',ast.Sub:'SUB',ast.Mult:'MUL',ast.FloorDiv:'DIV',ast.Mod:'MOD'}[type(n.op)],line=line)
            elif isinstance(n,ast.Compare) and len(n.ops)==1 and type(n.ops[0]) in (ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE):
                walk(n.left); walk(n.comparators[0]); emit({ast.Eq:'EQ',ast.NotEq:'NE',ast.Lt:'LT',ast.LtE:'LE',ast.Gt:'GT',ast.GtE:'GE'}[type(n.ops[0])],line=line)
            else: raise CompileError(f'Line {line}: unsupported expression; use integers, strings, variables, arithmetic or one comparison')
        walk(tree)
    if mode=='assembly':
        for line,raw in enumerate(source.splitlines(),1):
            raw=raw.strip()
            if not raw or raw.startswith('#'): continue
            parts=raw.split(maxsplit=1); op=parts[0].upper()
            if op not in OPS: raise CompileError(f'Line {line}: unknown instruction {op}')
            arg=None
            if len(parts)==2:
                try: arg=json.loads(parts[1])
                except json.JSONDecodeError: arg=parts[1]
            emit(op,arg,line)
        validate(code)
        return code
    if mode not in ('beginner','highlevel'): raise CompileError('Unknown educational language')
    for line,raw in enumerate(source.splitlines(),1):
        text=raw.strip()
        if not text or text.startswith('#'): continue
        if mode=='highlevel':
            text=text.removesuffix(';').strip()
            text=re.sub(r'^let\s+(\w+)\s*=\s*',r'set \1 to ',text)
            if text.startswith('print(') and text.endswith(')'): text='show '+text[6:-1]
        if text.startswith('set '):
            m=re.fullmatch(r'set ([A-Za-z_]\w*) to (.+)',text)
            if not m: raise CompileError(f'Line {line}: use set name to expression')
            expr(m[2],line); emit('STORE',m[1],line)
        elif text.startswith('show '): expr(text[5:],line); emit('PRINT',line=line)
        elif text.startswith(('while ','if ')):
            kind,condition=text.split(' ',1); start=len(code); expr(condition,line)
            blocks.append((kind,start,emit('JZ',0,line)))
        elif text=='else':
            if not blocks or blocks[-1][0]!='if': raise CompileError(f'Line {line}: else requires if')
            _,start,jump=blocks.pop(); end=emit('JMP',0,line); code[jump]['arg']=len(code); blocks.append(('else',start,end))
        elif text=='end':
            if not blocks: raise CompileError(f'Line {line}: unmatched end')
            kind,start,jump=blocks.pop()
            if kind=='while': emit('JMP',start,line)
            code[jump]['arg']=len(code)
        else: raise CompileError(f'Line {line}: unknown command')
    if blocks: raise CompileError('Missing end for if or while block')
    emit('HALT'); validate(code)
    return code


def validate(code):
    if not isinstance(code,list) or not 1<=len(code)<=10000: raise CompileError('Program must contain 1–10000 instructions')
    for i,item in enumerate(code):
        if not isinstance(item,dict) or item.get('op') not in OPS: raise CompileError(f'Invalid instruction {i}')
        op,arg=item['op'],item.get('arg')
        if op in ('JMP','JZ') and (type(arg)!=int or not 0<=arg<len(code)): raise CompileError(f'Invalid jump at {i}')
        if op in ('LOAD','STORE') and (not isinstance(arg,str) or not re.fullmatch(r'[A-Za-z_]\w*',arg)): raise CompileError(f'Invalid variable at {i}')
        if op=='PUSH' and type(arg) not in (int,str,bool): raise CompileError(f'Invalid constant at {i}')
        if op not in ('JMP','JZ','LOAD','STORE','PUSH') and arg is not None: raise CompileError(f'{op} takes no operand')
    return code


def encode(code):
    validate(code)
    return b'TCMP\x01'+json.dumps(code,separators=(',',':')).encode()


def decode(data):
    if not data.startswith(b'TCMP\x01'): raise CompileError('Invalid TriCompile bytecode header')
    try: return validate(json.loads(data[5:]))
    except (ValueError,UnicodeError) as e: raise CompileError(f'Invalid bytecode: {e}') from e


class Machine:
    def __init__(self,code):
        self.code=validate(code); self.pc=0; self.stack=[]; self.variables={}; self.output=[]; self.steps=0; self.halted=False
    def step(self):
        if self.halted: return
        if self.steps>=10000: raise CompileError('Instruction limit reached (10000)')
        if not 0<=self.pc<len(self.code): raise CompileError('Program ended without HALT')
        item=self.code[self.pc]; op=item['op']; arg=item.get('arg'); self.pc+=1; self.steps+=1
        try:
            if op=='PUSH': self.stack.append(arg)
            elif op=='LOAD': self.stack.append(self.variables[arg])
            elif op=='STORE': self.variables[arg]=self.stack.pop()
            elif op=='PRINT': self.output.append(str(self.stack.pop()))
            elif op=='JMP': self.pc=arg
            elif op=='JZ':
                if not self.stack.pop(): self.pc=arg
            elif op=='HALT': self.halted=True
            else:
                b=self.stack.pop(); a=self.stack.pop()
                if op in ('SUB','MUL','DIV','MOD') and (type(a)!=int or type(b)!=int): raise ValueError('integer operands required')
                if op=='MUL' and (a.bit_length()+b.bit_length()>4096): raise ValueError('integer size limit')
                value={'ADD':lambda:a+b,'SUB':lambda:a-b,'MUL':lambda:a*b,'DIV':lambda:a//b,'MOD':lambda:a%b,'EQ':lambda:a==b,'NE':lambda:a!=b,'LT':lambda:a<b,'LE':lambda:a<=b,'GT':lambda:a>b,'GE':lambda:a>=b}[op]()
                if isinstance(value,str) and len(value)>10000: raise ValueError('string size limit')
                if type(value)==int and value.bit_length()>4096: raise ValueError('integer size limit')
                self.stack.append(value)
            if len(self.stack)>10000: raise ValueError('stack limit')
        except (KeyError,IndexError,TypeError,ValueError,ZeroDivisionError) as e:
            raise CompileError(f'Instruction {self.pc-1}, source line {item.get("line",0)}: {e}') from e
    def run(self):
        while not self.halted: self.step()
        return '\n'.join(self.output)
    def state(self):
        return {'pc':self.pc,'stack':self.stack,'variables':self.variables,'output':'\n'.join(self.output),'steps':self.steps,'halted':self.halted}
