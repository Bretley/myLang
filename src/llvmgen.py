from slr import SLRParser
from AST import AST
from AST import flattenLists
from AST import asts
from varClasses import *
from semantic import *
from typedef import Product, Sum
from defaults import isDefault
from symTable import SymbolTable, NamedSymbolTable

from llvmlite import ir

i32 = ir.IntType(32)
fp = ir.DoubleType()

conversions = {
        'Int': i32,
        'Float': fp
}





""" indent functions plus newline """

includes = ['stdarg', 'stdlib', 'stdio']
tab = ' '*4


def codegen(mod, ast, st, nst, ctx = None):
    """
    Args:
        ast: AST to read
        st: SymbolTable
        nst: NamedSymbolTable
    """
    if not isinstance(ast, AST):
        return None

    name = ast.name
    if name == 'program':
        codegen(mod, ast[0], st, nst, ctx)
    elif name == 'declaration-list':
        for child in ast:
            codegen(mod, child, st, nst, ctx)
    elif name == 'declaration':
        codegen(mod, ast[0], st, nst, ctx)
    elif name == 'fun-declaration':
        nst.enterScope(ast[0][0])
        r_type = conversions[ast[-1].type]
        call_sig = tuple(conversions[x] for x in ast[2][0].type)
        f_type = ir.FunctionType(i32, call_sig)
        f = ir.Function(mod, f_type, name=ast[0][0])
        block = f.append_basic_block(name="entry")

        builder = ir.IRBuilder(block)
        for i, arg_name in enumerate(ast[2][0].names):
            f.args[i].name = arg_name
        args = f.args
        ctx = {'builder': builder}
        codegen(mod, ast[2], st, nst, ctx)

    elif name == 'anonymous-function':
        codegen(mod, ast[2], st, nst, ctx)
    elif name == 'final-stmt':
        if ast[0].name == 'other-selection-stmt':
            codegen(mod, ast[0], st, nst, ctx)
        else:
            ctx['builder'].ret(codegen(mod, ast[0], st, nst, ctx))
    elif name == 'simple-expression':
        if ast.case(0):
            l = codegen(mod, ast[0], st, nst, ctx)
            r = codegen(mod, ast[2], st, nst, ctx)
            op = ast[1][0]
            return ctx['builder'].icmp_signed(op, l, r, )
        else:
            return codegen(mod, ast[0], st, nst, ctx)
    elif name == 'additive-expression':
        if ast.case(0):
            l = codegen(mod, ast[0], st, nst, ctx)
            r = codegen(mod, ast[2], st, nst, ctx)
            op = ast[1][0]
            if op == '+':
                return ctx['builder'].add(l,r)
            elif op == '-':
                return ctx['builder'].sub(l,r)
        else:
            return codegen(mod, ast[0], st, nst, ctx)
    elif name == 'term':
        if ast.case(0):
            l = codegen(mod, ast[0], st, nst, ctx)
            r = codegen(mod, ast[2], st, nst, ctx)
            op = ast[1][0]
            if op == '*':
                return ctx['builder'].mul(l,r)
            elif op == '/':
                return ctx['builder'].mul(l,r)
        else:
            return codegen(mod, ast[0], st, nst, ctx)
    elif name == 'factor':
        if ast.case(0):
            return codegen(mod, ast[1], st, nst, ctx)
        elif ast.case(1):  # Var access:
            return ast[0][0]
        elif ast.case(2):
            return None
        elif ast.case(3):
            return i32(int(ast[0]))
        elif ast.case(4):
            return i32(- int(ast[0]))

    """
    else:
        for child in ast:
            codegen(mod, child, st, nst, ctx)
    """


parser = SLRParser("grammar.txt", sys.argv[1])
ast = parser.parse()[0]
ast.genCases(parser.grammar)





flattenedListAST = flattenLists(ast)[0]
flattenedListAST.genCases(parser.grammar)
st = SymbolTable()
nst = NamedSymbolTable()


valid = errorCheck(flattenedListAST,
        st,
        nst,
        parser.lexer.infileLines)


module = ir.Module(name='Default')
codegen(module, flattenedListAST, st, nst)
print(module)
print(module.functions)

"""
f2 = ir.FunctionType(i32, (i32, i32))
f = ir.Function(module, f2, name='foo')
block = f.append_basic_block(name="entry")
build = ir.IRBuilder(block)
build.add(
    build.add(
        i32(5), i32(7), 'add_tmp'),
    i32(7),
    'addtmp')
    
"""
print(module)
