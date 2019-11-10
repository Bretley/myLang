import sys
from slr import *

def isBool(*args):
    print( args)
    return all([x.type == 'boolean' for x in args])

class Var:
    def __init__(self, name, varType):
        self.name = name
        self.type = varType
class Fun:
    def __init__(self, name, varType, paramNum):
        self.name = name
        self.type = varType
        self.paramNum = paramNum
        self.params = []

""" Checks type and marks ast """
def typeOf(ast):
    if ast.type:
        return ast.type
        # Hasty return
    
    if ast.name == 'compound-stmt':
        ast.type = typeOf(ast[0]) # type of final-stmt
    elif ast.name == 'final-stmt':
        ast.type = typeOf(ast[0]) # simple-expression
    elif ast.name == 'simple-expression':
        if len(ast.children) == 1:
            ast.type = typeof(ast[0])
    return ast.type

     

class SymbolTable:
    def __init__(self):
        self.stack = []
        self.stackNum = -1
    def enterScope(self):
        self.stack.append({})
        self.stackNum += 1
    def exitScope(self):
        self.stack.pop()
        self.stackNum -= 1
    def findSymbol(self,symbol):
        for nested in reversed(self.stack):
            if symbol in nested:
                return nested[symbol]
        return None
    def addSymbol(self,symbol):
        self.stack[self.stackNum][symbol.name] = symbol
    def checkScope(self,symbolName):
        if symbolName in self.stack[-1]:
            return True
        else:
            return False

def listLen(ast, name):
    ret = 0
    cur = ast
    while cur.name == name:
        cur = cur[0]
        ret += 1
        if not isinstance(cur, AST):
            break
    return ret

def errorCheck(ast, st):
    valid = True
    if not isinstance(ast, AST):
        return True

    if ast.name == 'program':
        st.enterScope()

    elif ast.name == 'fun-declaration':
        if len(ast[0].children) != 1 :
            print( "Error: only one name per function definition allowed")
            return False
        st.enterScope()

    if ast.name == 'final-stmt' and ast[0].name == 'other-selection-stmt':
        ast[0].selectionResolution = 'return'

    if ast.name == 'assignment' and ast[2].name == 'other-selection-stmt':
        ast[2].selectionResolution = ast[0]

    if ast.selectionResolution != None:
        for child in ast.children:
            if isinstance(child, AST):
                child.selectionResolution = ast.selectionResolution



    """ Top down above here """
    for child in ast:
        valid = valid and errorCheck(child, st)
        if not valid:
            return False
    """ Bottom up below here """

    """ Function declaration / body """

    if ast.name == 'param-list':
        #print( ast)
        pass

    elif ast.name == 'param':
        for name in ast[1]:
            #print( name + ast[0].brackets)
            st.addSymbol(Var(name, ast[0].baseType + ast[0].brackets))

    elif ast.name == 'fun-declaration':
        ast.returnType = ast[2].type

    elif ast.name == 'anonymous-function':
        ast.type = ast[2].type

    elif ast.name == 'compound-stmt':
        ast.type = ast[3].type

    elif ast.name == 'final-stmt':
        ast.type = ast[0].type

    elif ast.name == 'boolExpression':
        print( ast)
        if ast.case(0):
            if isBool(ast[0], ast[2]):
                ast.type == 'boolean'
            else:
                print('ERROR: non boolean clauses')
        else:
            if isBool(ast[0]):
                ast.type == 'boolean'
            else:
                print('ERROR: non boolean clauses')

    elif ast.name == 'boolTerm':
        # TODO: actually type check the tree
        ast.type == 'boolean'

    elif ast.name == 'boolFactor':
        if ast.case(0) and isBool(ast[0]):
            ast.type == 'boolean'
        elif isBool(ast[1]):
            ast.type == 'boolean'
        else:
            print( 'ERROR')

    elif ast.name == 'simple-expression':
        if len(ast) == 1:
            ast.type = ast[0].type
        else:
            ast.type = 'boolean'

    elif ast.name == 'additive-expression':
        if len(ast) == 1:
            ast.type = ast[0].type
        else: 
            if ast[0].type == ast[2].type:
                ast.type =  ast[0].type
            else:
                print('ERROR')

    elif ast.name == 'term':
        if len(ast) == 1:
            ast.type = ast[0].type
        else:
            if ast[0].type == ast[2].type:
                ast.type =  ast[0].type
            else:
                print('ERROR')

    elif ast.name == 'factor':
        # TODO: fix fix fix
        if len(ast) == 1:
            if isinstance(ast[0], AST) and ast[0].name == 'var':
                if st.checkScope(ast[0][0]):
                    ast.type  = st.findSymbol(ast[0][0]).type
            elif not isinstance(ast[0], AST):
                ast.type = 'int'
                    
            else:
                ast.type = 'int'
        #TODO: Else
        else:
            ast.type = 'int'
            # if ast[0].type == ast[2].type:
                # ast.type =  ast[0].type
            # else: print('ERROR')
        #print( '====' + ast.type + '====')
    elif ast.name == 'other-selection-stmt':
        ast.type = ast[1].type

    elif ast.name == 'final-clause':
        ast.type = ast[3].type

    elif ast.name == 'assignment':
        ast.type = []
        for child in ast[2]:
            if child.isdigit():
                ast.type.append('int')
    elif ast.name == 'var-declaration':
        for name in ast[1]:
            if st.checkScope(name):
                print("ERROR: " + name + ' already defined in this scope')
                return False
            else:
                st.addSymbol(Var(name, ast[0].baseType + ast[0].brackets))

    elif ast.name == 'bracket-group':
        if len(ast.children) == 2:
            ast.length = ''
        else:
            ast.length = ast[1]
        ast.singlet = ''.join(ast.children)
    elif ast.name == 'type-specifier':
        ast.baseType = ast[0].lower()
        ast.dimensions = len(ast[1].children)
        ast.brackets = ''.join([singlet.singlet for singlet in ast[1]])


    elif ast.name == 'fun-declaration':
        st.exitScope()
    if ast.name == 'program':
        st.exitScope()
    return valid
