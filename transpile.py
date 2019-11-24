from slr import SLRParser
from AST import AST
from AST import flattenLists
from AST import asts
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
            for childname in nameList:
                varList.append(str(typeInfo) + ' ' + 
                        str(childname) +
                        '[]'*typeInfo.dimensions)
        ret += ', '.join(varList)
        ret += ')'
        return ret


def genC(ast, st, tabDepth):
    ret = ''
    if not isinstance(ast, AST):
        return ''
    name = ast.name
    if name == 'program':
        st.enterScope()

    if name == 'var-declaration':
        for childname in ast[1]:
            st.addSymbol(Var(name, ast[0].baseType + ast[0].brackets,0))
    elif name == 'assignment':
        for childname, value, typ in zip(ast[0],ast[2], ast.type):
            if not st.checkScope(name):
                ret += typ + ' ' + childname + ' = ' + value + ';\n'
                st.addSymbol(Var(childname, typ,0))
            else:
                ret += childname + ' = ' + value + ';\n'
    elif name == 'fun-declaration':
        ret += '\n' + ast.returnType.lower().replace('[]','*') + ' ' + ast[0][0] + str(Function(ast[2]).params) + ' {\n'
        tabDepth += 1

    if name == 'final-stmt' and ast[0].name == 'other-selection-stmt':
        ast[0].selectionResolution = 'return'

    if name == 'assignment' and ast[2].name == 'other-selection-stmt':
        ast[2].selectionResolution = ast[0]

    if ast.selectionResolution != None:
        for child in ast.children:
            if isinstance(child, AST):
                child.selectionResolution = ast.selectionResolution

    if name == 'expressionList':
        if ast[-1].name == 'other-selection-stmt':
            ast[-1].selectionResolution = ''

    if name == 'iteration-stmt':
        tabDepth += 1


    """ top down above """
    for child in ast:
        ret += genC(child, st, tabDepth)
    """ bottom up below """

    if name == 'anonymous-function':
        ast.cstr = ast[2].cstr
        ret += ast.cstr
    elif name == 'function-body':
        ast.cstr = ast[1].cstr + ast[2].cstr
    elif name == 'local-declarations-list':
        ast.cstr = ((tab*tabDepth)+"\n").join([x.cstr for x in ast])
    elif name == 'iteration-stmt':
        if ast.case(0):
            ast.cstr = (tab*(tabDepth-1))
            ast.cstr += 'while ' + ast[2].cstr + ' {\n' 
            ast.cstr += ast[5].cstr
            ast.cstr += '\n' + (tab*(tabDepth-1)) + '}\n'
    elif name == 'final-stmt':
        #TODO figure out the casese
        # If this is the last one in a function and only contains a simple
        # expression, we ought to return it
        if ast[0].name == 'other-selection-stmt':
            ast.cstr = ast[0].cstr
        elif ast.selectionResolution in ['return', None]:
            ast.cstr = 'return ' +  ast[0].cstr + ';\n'
        else: 
            ast.cstr = 'selectionResolution ' + ast[0].cstr
        #ret += tab*tabDepth + 'return ' + ast[0].cstr + ';\n'

    elif ast.name in ['addop','relop','mulop']:
        ast.cstr = ast[0]
    elif ast.name in ['factor']:
        if isinstance(ast[0], AST):
            ast.cstr = ast[0].cstr
        elif len(ast) > 1:
            if ast[0] == '-':
                ast.cstr = ''.join(ast.children)
            else:
                ast.cstr = ast[1].cstr
        else:
            ast.cstr = ast[0]
    elif name == 'call':
        ast.cstr = ast[0].cstr + ast[1] + ast[2].cstr + ast[3]
    elif name == 'args':
        ast.cstr = ast[0].cstr
    elif name == 'arg-list':
        ast.cstr = ','.join([x.cstr for x in asts(ast)])
    elif name == 'statement-list':
        ast.cstr = '\n'.join([x.cstr for x in ast])
    elif name == 'statement':
        ast.cstr = ast[0].cstr
    elif name == 'expression-stmt':
        ast.cstr = (tab*tabDepth) +ast[0].cstr + ';'
    elif name == 'expressionList':
        if ast[-1].name == 'other-selection-stmt':
            resolved = ' = '.join([x.cstr + '' for x in asts(ast[:-1])])
            print( resolved)
            ast.cstr = ast[-1].cstr.replace('selectionResolution', resolved + ' =' )
        elif len(ast) > 1:
            ast.cstr = ' = '.join([x.cstr for x in asts(ast)])
        else:
            ast.cstr = ast[0].cstr
            # 
    elif name == 'var-declaration':
        ast.cstr = '' 
        for childname in ast[1]:
            ast.cstr += tab*tabDepth
            ast.cstr += st.findSymbol(childname).type + ' ' + childname
            ast.cstr += ';\n'
    elif name == 'var':
        if ast.case(0):
            ast.cstr = ast[0] + ast[1].cstr
    elif name == 'bracket-list':
        ast.cstr = ''.join([x.cstr for x in ast])
    elif name == 'bracket-group':
        if ast.case(0):
            ast.cstr = '[]'
        else:
            ast.cstr = '[' + ast[1] +']'

    elif name in ['term','additive-expression']:#'simple-expression']:
        if len(ast) == 1:
            ast.cstr = ast[0].cstr
        elif len(ast) == 3:
            ast.cstr =  '(' +ast[0].cstr + ast[1].cstr +ast[2].cstr + ')'
        elif len(ast) == 5:
            ast.cstr =  '(' +ast[1].cstr + ast[2].cstr +ast[3].cstr + ')'
    elif name == 'simple-expression':
        if ast.case(0):
            ast.cstr =    '(' +ast[0].cstr + str(ast[1][0]) +ast[2].cstr + ')'
        elif ast.case(1):
            ast.cstr =   '' + ast[0].cstr + ''

    elif name == 'expression':
        if len(ast) == 1:
            ast.cstr = ast[0].cstr
        else:
            #TODO: Type check assignment expression
            pass
    elif name == 'other-selection-stmt':
        ast.cstr = ast[0].cstr
        ast.cstr += ' else ' + ast[1].cstr
        pass
    elif name == 'clause-list':
        for index, child in enumerate(ast):
            if index == 0:
                ast.cstr = tab*tabDepth + 'if '+ child.cstr
            else:
                ast.cstr += ' else if ' + child.cstr
    elif name == 'boolTermList':
        if len(ast) > 1:
            ast.cstr = '(' + ' && '.join([x.cstr for x in asts(ast)]) + ')'
        else:
            ast.cstr = ast[0].cstr

    elif name == 'boolExprList':
        if len(ast) > 1:
            ast.cstr = '(' + ' || '.join([x.cstr for x in asts(ast)]) + ')'
        else:
            ast.cstr = ast[0].cstr
    elif name == 'boolFactor':
        if ast.case(0):
            ast.cstr = ast[0].cstr
        elif ast.case(1):
            ast.cstr = '(!' + ast[1].cstr + ')'  
        else:
            ast.cstr = '(' + ast[1].cstr + ')'
    elif name == 'final-clause':
        ast.cstr = '{\n'
        if ast[3][0].name == 'other-selection-stmt':
            ast.cstr = '{\n' + tab*tabDepth + ast[3].cstr.replace('\n','\n'+(tab))
            ast.cstr += '\n' + tab*(tabDepth) +'}'
        else:
            if ast.selectionResolution != 'return':
                ast.cstr += tab*(tabDepth+1)
                ast.cstr += ast[3].cstr + ';\n'
            else:
                if ast[3].name != 'other-selection-stmt':
                    ast.cstr += tab*(tabDepth+1)
                    ast.cstr += ast[3].cstr
            ast.cstr += tab*(tabDepth) + '}' 

    elif name == 'clause':
        ast.cstr = ast[2].cstr + ' {\n'
        if ast[5][0].name == 'other-selection-stmt':
            ast.cstr += tab*tabDepth + ast[5].cstr.replace('\n','\n'+(tab))
            ast.cstr += '\n' + tab*(tabDepth) +'}'
        else:
            if ast.selectionResolution != 'return':
                ast.cstr += tab*(tabDepth+1)
                ast.cstr += ast[5].cstr
                ast.cstr += ';\n'
            else:
                if ast[5].name != 'other-selection-stmt':
                    ast.cstr += tab*(tabDepth+1)
                    ast.cstr += ast[5].cstr
            ast.cstr += tab*(tabDepth) + '}' 

    elif name == 'fun-declaration':
        ret += '\n}\n'
        tabDepth -= 1

    return ret

parser = SLRParser("grammar.txt", sys.argv[1])
ast = parser.parse()[0]
ast.genCases(parser.grammar)

flattenedListAST = flattenLists(ast, False, None)[0]
flattenedListAST.genCases(parser.grammar)
valid =  errorCheck(flattenedListAST,
        SymbolTable(),
        parser.lexer.infileLines)

if valid:
 print( genC (flattenedListAST, SymbolTable(), 0))


