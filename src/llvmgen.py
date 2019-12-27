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
boolean = ir.IntType(1)

conversions = {
    'Int': i32,
    'Float': fp,
    'Bool': boolean
}





""" indent functions plus newline """

includes = ['stdarg', 'stdlib', 'stdio']
tab = ' '*4


def binop(ast, nst, ctx = None):
    l = codegen(ast[0], nst, ctx)
    r = codegen(ast[2], nst, ctx)
    if isinstance(ast[1], AST):
        op = ast[1][0]
    else:
        op = ast[1]
    return (l, r, op)

def conjunctive_bool(ast, nst, ctx):
    if len(ast) == 1:
        return codegen(ast[0], nst, ctx)
    else:
        l, r, op = binop(ast, nst, ctx)
        lhs = ctx['builder'].and_(l, r)
        if op == 'v':
            f = ctx['builder'].or_
        elif op == '^':
            f = ctx['builder'].and_
        for rhs in asts(ast)[2:]:
            rhs = codegen(rhs, nst, ctx)
            lhs = f(lhs, rhs)
        return lhs


def codegen(ast, nst, ctx=None):
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
        codegen(ast[0], nst, ctx)
    elif name == 'declaration-list':
        for child in ast:
            codegen(child, nst, ctx)
    elif name == 'declaration':
        codegen(ast[0], nst, ctx)
    elif name == 'fun-declaration':
        nst.enterScope(ast[0][0])
        r_type = conversions[ast[-1].type]
        call_sig = tuple(conversions[x] for x in ast[2][0].type)
        f_type = ir.FunctionType(conversions[ast.returnType], call_sig)
        f = ir.Function(ctx['mod'], f_type, name=ast[0][0])
        block = f.append_basic_block(name="entry")

        builder = ir.IRBuilder(block)
        for i, arg_name in enumerate(ast[2][0].names):
            f.args[i].name = arg_name
        args = f.args
        ctx = {'builder': builder, 'fun': f}
        codegen(ast[2], nst, ctx)

    elif name == 'anonymous-function':
        codegen(ast[2], nst, ctx)
    elif name == 'final-stmt':
        if ast[0].name == 'other-selection-stmt':
            codegen(ast[0], nst, ctx)
        else:
            ctx['builder'].ret(codegen(ast[0], nst, ctx))
    elif name == 'expressionList':
        if ast[-1] == 'other-selection-stmt':
            pass
        elif ast[-1] == 'constructor':
            pass
        else:
            result = codegen(ast[-1], nst, ctx)
        for x in asts(ast[:-1]):
            pass  # DO some kind of lwd/swd
        return result

    elif name in ['boolTermList', 'boolExprList']:
        return conjunctive_bool(ast, nst, ctx)

    elif name == 'boolFactor':
        print('boolfact')
        if ast.case(0):
            return codegen(ast[0], nst, ctx)
        elif ast.case(1):
            res = codegen(ast[0], nst, ctx)
            return ctx['builder'].not_(res)
        elif ast.case(2):
            return codegen(ast[1], nst, ctx)

    elif name == 'simple-expression':
        if ast.case(0):
            l, r, op = binop(ast, nst, ctx)
            return ctx['builder'].icmp_signed(op, l, r)
        else:
            return codegen(ast[0], nst, ctx)
    elif name == 'additive-expression':
        if ast.case(0):
            l, r, op = binop(ast, nst, ctx)
            if op == '+':
                return ctx['builder'].add(l, r)
            elif op == '-':
                return ctx['builder'].sub(l, r)
        else:
            return codegen(ast[0], nst, ctx)
    elif name == 'term':
        if ast.case(0):
            l, r, op = binop(ast, nst, ctx)
            if op == '*':
                return ctx['builder'].mul(l, r)
            elif op == '/':
                return ctx['builder'].sdiv(l, r)
        else:
            return codegen(ast[0], nst, ctx)
    elif name == 'factor':
        if ast.case(0):
            return codegen(ast[1], nst, ctx)
        elif ast.case(1):  # Var access:
            # Param case
            p = [x for x in ctx['fun'].args if x.name == ast[0][0]][0]
            return p

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
codegen(flattenedListAST, nst, {'mod': module})
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
