from slr import SLRParser
from AST import AST
from AST import flattenLists
from semantic import *
import sys

tab = ' '*4

# Final statement or return statement
class Body:
    def __init__(self, funBodyASTNode):
        self.type = funBodyASTNode.type

class Function:
    def __init__(self, anonymousFunctionASTNode):
        self.params = Parameters(anonymousFunctionASTNode[0])
        self.body =  Body(anonymousFunctionASTNode[2])
        self.returnType = self.body.type

class Type: 
    def __init__(self, typeSpecifierASTNode):
        self.baseType = typeSpecifierASTNode[0]
        #print( typeSpecifierASTNode[1])
        self.dimensions = len(typeSpecifierASTNode[1].children)

    def __eq__(self, other):
        return (self.dimensions == other.dimensions and
                self.baseType == other.baseType)

    def __str__(self):
        return self.baseType.lower()


class Parameters:
    def __init__(self, paramASTNode):
        self.params = []
        for param in paramASTNode[0]:
            if param != ',':
                self.params.append((Type(param[0]), param[1].children))

    def __str__(self):
        ret = '('
        varList = []
        for typeInfo, nameList in self.params:
            for name in nameList:
                varList.append(str(typeInfo) + ' ' + str(name) +
                        '[]'*typeInfo.dimensions)
        ret += ', '.join(varList)
        ret += ')'
        return ret


def genC(ast, st, tabDepth):
    ret = ''
    if not isinstance(ast, AST):
        return ''
    if ast.name == 'program':
        st.enterScope()

    if ast.name == 'var-declaration':
        for name in ast[1]:
            st.addSymbol(Var(name, ast[0].baseType + ast[0].brackets))
            ret += ast[0].baseType + ' ' + name + ast[0].brackets
            ret += ';\n'
    elif ast.name == 'assignment':
        for name, value, typ in zip(ast[0],ast[2], ast.type):
            if not st.checkScope(name):
                ret += typ + ' ' + name + ' = ' + value + ';\n'
                st.addSymbol(Var(name, typ))
            else:
                ret += name + ' = ' + value + ';\n'
    elif ast.name == 'fun-declaration':
        ret += '\n' + ast.returnType.lower().replace('[]','*') + ' ' + ast[0][0] + str(Function(ast[2]).params) + ' {\n'
        tabDepth += 1


    """ top down above """
    for child in ast:
        ret += genC(child, st, tabDepth)
    """ bottom up below """

    if ast.name == 'anonymous-function':
        ast.cstr = ast[2].cstr
        ret += ast.cstr
    if ast.name == 'final-stmt':
        #TODO figure out the casese
        # If this is the last one in a function and only contains a simple
        # expression, we ought to return it
        if ast[0].name == 'other-selection-stmt':
            ast.cstr = ast[0].cstr
        elif ast.selectionResolution in ['return', None]:
            ast.cstr = 'return ' +  ast[0].cstr + ';\n'
        else: 
            ast.cstr = ast.selectionResolution + ' = ' + ast[0].cstr
        #ret += tab*tabDepth + 'return ' + ast[0].cstr + ';\n'

    if ast.name in ['addop','relop','mulop']:
        ast.cstr = ast[0]
    if ast.name in ['factor']:
        #print( ast)
        if isinstance(ast[0], AST):
            ast.cstr = ast[0].cstr
        elif len(ast) > 1:
            if ast[0] == '-':
                ast.cstr = ''.join(ast.children)
            else:
                ast.cstr = ast[1].cstr
        else:
            ast.cstr = ast[0]
    elif ast.name == 'call':
        ast.cstr = ast[0].cstr + ast[1] + ast[2].cstr + ast[3]
    elif ast.name == 'args':
        ast.cstr = ast[0].cstr
    elif ast.name == 'arg-list':
        ast.cstr = ','.join([x.cstr for x in ast if isinstance(x,AST)])
    elif ast.name == 'var':
        if ast.case(0):
            ast.cstr = ast[0]
        else:
            ast.cstr = ast[0] + ast[1] + ast[2].cstr + ast[3]
            print( ast)

    if ast.name in ['term','additive-expression']:#'simple-expression']:
        if len(ast) == 1:
            ast.cstr = ast[0].cstr
        elif len(ast) == 3:
            ast.cstr =  '(' +ast[0].cstr + ast[1].cstr +ast[2].cstr + ')'
        elif len(ast) == 5:
            ast.cstr =  '(' +ast[1].cstr + ast[2].cstr +ast[3].cstr + ')'
    elif ast.name == 'simple-expression':
        if len(ast) == 1:
            print( ast)
            ast.cstr =   '' + ast[0].cstr + ''
        elif len(ast) == 3:
            ast.cstr =    '(' +ast[0].cstr + str(ast[1][0]) +ast[2].cstr + ')'
        elif len(ast) == 5:
            ast.cstr =  '(' +ast[1].cstr + str(ast[2][0]) +ast[3].cstr + ')'

    elif ast.name == 'expression':
        if len(ast) == 1:
            ast.cstr = ast[0].cstr
        else:
            #TODO: Type check assignment expression
            pass
    elif ast.name == 'other-selection-stmt':
        ast.cstr = ast[0].cstr
        ast.cstr += ' else ' + ast[1].cstr
        pass
    elif ast.name == 'clause-list':
        for index, child in enumerate(ast):
            if index == 0:
                ast.cstr = tab*tabDepth + 'if '+ child.cstr
            else:
                ast.cstr += ' else if ' + child.cstr
    elif ast.name == 'boolTermList':
        if ast.case(0):
            ast.cstr = '(' + ' && '.join([x.cstr for x in ast if isinstance(x, AST)]) + ')'
        else:
            ast.cstr = ast[0].cstr

    elif ast.name == 'boolExprList':
        if ast.case(0):
            ast.cstr = '(' + ' || '.join([x.cstr for x in ast if isinstance(x, AST)]) + ')'
        else:
            ast.cstr = ast[0].cstr
    elif ast.name == 'boolFactor':
        if ast.case(0):
            ast.cstr = ast[0].cstr
        elif ast.case(1):
            ast.cstr = '(!' + ast[1].cstr + ')'  
        else:
            ast.cstr = '(' + ast[1].cstr + ')'
    elif ast.name == 'final-clause':
        ast.cstr = '{\n'
        if ast[3][0].name == 'other-selection-stmt':
            ast.cstr = '{\n' + tab*tabDepth + ast[3].cstr.replace('\n','\n'+(tab))
            ast.cstr += '\n' + tab*(tabDepth) +'}'
        else:
            if ast.selectionResolution != 'return':
                ast.cstr += tab*(tabDepth+1) + ast.selectionResolution
                ast.cstr += '=' + ast + ';\n'
            else:
                if ast[3].name != 'other-selection-stmt':
                    ast.cstr += tab*(tabDepth+1)
                    ast.cstr += ast[3].cstr
            ast.cstr += tab*(tabDepth) + '}' 

    elif ast.name == 'clause':
        ast.cstr = ast[2].cstr + ' {\n'
        if ast.selectionResolution != 'return':
            ast.cstr += tab*(tabDepth+1) + ast.selectionResolution
            ast.cstr += '=' + ast + ';\n'
        else:
            if ast[5].name != 'other-selection-stmt':
                ast.cstr += tab*(tabDepth+1)
                ast.cstr += ast[5].cstr
        ast.cstr += tab*(tabDepth) + '}' 


    elif ast.name == 'fun-declaration':
        ret += '\n}\n'
        tabDepth -= 1

    return ret

parser = SLRParser("grammar.txt", sys.argv[1])
ast = parser.parse()[0]
ast.genCases(parser.grammar)

flattenedListAST = flattenLists(ast, False, None)[0]
flattenedListAST.genCases(parser.grammar)
valid =  errorCheck(flattenedListAST, SymbolTable())

if valid:
 print( genC (flattenedListAST, SymbolTable(), 0))
#print([x for x in flattenedListAST[0][0][0])
#print( genC(flattenedListAST[0], SymbolTable(), 0))


