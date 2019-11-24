import sys
from slr import *
from AST import asts


def err(errString): 
    print( "ERROR: " + errString)

def isBool(*args):
    if isinstance(args[0], list):
        return all([x.type == 'boolean' for x in args[0]])
    else:
        return all([x.type == 'boolean' for x in args])

def allType(checkList, ast):
    return all(asts(ast))

class Var:
    def __init__(self, name, baseType, dimensions):
        self.name = name
        self.type = baseType
        self.dimensions = dimensions
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

def errorCheck(ast, st, fileLines):
    valid = True
    if not isinstance(ast, AST):
        return True

    if ast.name == 'program':
        st.enterScope()

    elif ast.name == 'fun-declaration':
        if len(ast[0].children) != 1 :
            err( "only one name per function definition allowed")
            return False
        st.enterScope()


    """ Top down above here """
    for child in ast:
        valid = valid and errorCheck(child, st, fileLines)
        if not valid:
            return False
    """ Bottom up below here """

    """ Function declaration / body """
    
    for x in asts(ast):
        ast.hoists += x.hoists
    if ast.name == 'param-list':
        pass

    elif ast.name == 'param':
        for childname in ast[1]:
            #print( name + ast[0].brackets)
            st.addSymbol(Var(childname, ast[0].baseType,
                ast[0].dimensions))

    elif ast.name == 'fun-declaration':
        # print( ast.hoists[0].name )
        # print( ast.hoists[0].type )
        ast.returnType = ast[2].type

    elif ast.name == 'anonymous-function':
        ast.type = ast[2].type

    elif ast.name == 'compound-stmt':
        ast.type = ast[3].type

    elif ast.name == 'function-body':
        ast.type = ast[2].type

    elif ast.name == 'final-stmt':
        ast.type = ast[0].type
    
    elif ast.name == 'expressionList':
        
        if len(ast) == 1:
            ast.type = ast[0].type
        else:
            #TODO: give this a look over
            checkType = ast[-1].type
            for varName in asts(ast)[:-1]:
                var = st.findSymbol(varName[0])
                if var is None: #Doesn't exist yet
                    st.addSymbol(Var(varName[0], checkType, 0)) # TODO: deal with multi dimensions
                    ast.hoists.append(st.findSymbol(varName[0]))
                else: # already defined
                    if var.type != checkType:
                        err("Attempting to assign expression of type: " + checkType + " -> " +
                                var.type)
                        print( ast.lineNum)
                        print( fileLines[ast[0].lineNum-1])

                        return False
            ast.type = ast[-1].type
        
    elif ast.name == 'boolExprList':
        if len(ast) == 1:
            ast.type = ast[0].type
        else:
            if isBool(asts(ast)):
                ast.type = 'boolean'
            else:
                print( 'ERROR: or clauses without bool type' )

    elif ast.name == 'boolTermList':
        if len(ast) == 1:
            ast.type = ast[0].type
        else:
            if isBool(asts(ast)):
                ast.type = 'boolean'
            else:
                print( 'ERROR TBD')

    elif ast.name == 'boolFactor':
        if ast.case(0):
            if isBool(ast[0]):
                ast.type = 'boolean'
            else: 
                ast.type = ast[0].type 
        elif ast.case(1):
            if isBool(ast[1]):
                ast.type = 'boolean'
            else:
                ast.type = ast[1].type
        else:
            ast.type = ast[1].type
        # print( '============')
        # print( ast.type)
        # print( ast)


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
        if ast.case(0):
            ast.type = ast[1].type
        elif ast.case(1):
            if isinstance(ast[0], AST) and ast[0].name == 'var':
                if st.checkScope(ast[0][0]):
                    var = st.findSymbol(ast[0][0])
                    ast.type = var.type + '[]'*(var.dimensions - len(ast[0][1]))
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
        for childname in ast[1]:
            if st.checkScope(childname):
                print("ERROR: " + childname + ' already defined in this scope')
                return False
            else:
                st.addSymbol(Var(childname, ast[0].baseType,
                    ast[0].dimensions))

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
