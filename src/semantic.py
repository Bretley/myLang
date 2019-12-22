import sys
from slr import *
from AST import asts
from varClasses import *
from errors import *
from typedef import *
from symTable import *


e = Error(sys.argv[1])
def isBool(*args):
    if isinstance(args[0], list):
        return all([x.type == 'Bool' for x in args[0]])
    else:
        return all([x.type == 'Bool' for x in args])

""" Checks type and marks ast """
def typeOf(ast):
    if ast.type:
        return ast.type
    if ast.name in ['compound-stmt', 'final-stmt']:
        ast.type = typeOf(ast[0]) # type of final/compound
    elif ast.name == 'simple-expression' and len(ast.children) == 1:
        ast.type = typeof(ast[0])
    return ast.type

def listLen(ast, name):
    ret = 0
    cur = ast
    while cur.name == name:
        cur = cur[0]
        ret += 1
        if not isinstance(cur, AST):
            break
    return ret

def errorCheck(ast, st, namedST, fileLines):
    valid = True
    if not isinstance(ast, AST):
        return True

    if ast.name == 'program':
        st.enterScope()
    elif ast.name == 'productType':
        st.enterScope()
        namedST.addScope(ast[1], {})
        namedST.enterScope(ast[1])

    elif ast.name == 'fun-declaration':
        if len(ast[0].children) != 1 :
            err( "only one name per function definition allowed")
            return False
        st.enterScope()
        namedST.addScope(ast[0][0],{})
        namedST.enterScope(ast[0][0])

    """ Top down above here """
    for child in ast:
        valid = valid and errorCheck(child, st, namedST, fileLines)
        if not valid:
            return False
    """ Bottom up below here """

    for x in asts(ast):
        ast.hoists += x.hoists
    
    if ast.name == 'param-list':
        pass

    elif ast.name == 'productType':
        namedST.setScope(st.exitScope())
        namedST.exitScope()
        st.addSymbol(Product(ast, st))
    elif ast.name == 'sumType':
        st.addSymbol(Sum(ast,st))
    elif ast.name == 'constructor':
        symbol = st.findSymbol(ast[0])
        if symbol is None:
            e.err("Constructor error\n" +
                    'type ' + ast[0] + ' not defined' ,
                    "Semantic",
                    ast.lineNum)
        elif ast[2].type != symbol.signatures:
            print( symbol.signatures)
            print( ast[2].type)
            e.err("Constructor error\n" + 
                    "No valid constructor of type: " + str(ast[2].type) + '\n' +
                    "found for type " + symbol.name + "\n",
                    "Semantic",
                    ast.lineNum)
        else:
            ast.type = ast[0]

    elif ast.name == 'namedParam':
        for childname in ast[1]:
            #print( name + ast[0].brackets)
            if not st.checkScope(childname): 
                st.addSymbol(Var(childname, ast[0].baseType,
                    ast[0].dimensions, 'param'))
            else:
                # TODO: Error msg for parameters with same name
                print( 'renamed param')
    elif ast.name == 'destructuredParam':
        if ast[0].dimensions > 0:
            #TODO: error message for
            # type specifier with dimension higher than 0
            # for  a destructured parameter
            print( 'higher dimension than 0 for destructure')
            pass
        elif isDefault(ast[0][0]):
            #TODO: error for default type in destructure
            print( 'defualt in param')
            pass
        typ = st.findSymbol(ast[0][0])
        if typ is None:
            #TODO: Error for type not being defined
            pass
        elif not isinstance(typ, Product):
            #TODO: error for must be product to be destructured
            print( 'not a product')
            pass
        else:
            for name in ast[2]:
                var = typ.get(name)
                if var is None:
                    #TODO: Error for illegal accessor name in destructure
                    pass
                elif st.checkScope(var.name):
                    #TODO: error for redefining param
                    # Does this even make sense? if you can't rename the param
                    # then no
                    pass
                else:
                    st.addSymbol(
                        Var(
                            var.name,
                            var.type,
                            var.dimensions,
                            'destructuredParam'
                        )
                    )

    elif ast.name == 'fun-declaration':
        namedST.setScope(st.exitScope())
        namedST.exitScope()
        ast.returnType = ast[2].type

    elif ast.name == 'anonymous-function':
        ast.type = ast[2].type
        if ast.parent.name != 'fun-declaration':
            i = 0
            if not st.checkScope('anonymous_main_' + str(i)):
                st.addSymbol(Var('anonymous_main_' + str(i), ast.type, 0, 'Function'))

    elif ast.name == 'compound-stmt':
        ast.type = ast[2].type

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
                    st.addSymbol(Var(varName[0], checkType, 0, 'hoisted')) # TODO: deal with multi dimensions
                    ast.hoists.append(st.findSymbol(varName[0]))
                else: # already defined
                    if var.type != checkType:
                        print( var.name)
                        print( var.type)
                        print( st.stack)
                        print("Attempting to assign expression of type: " + checkType + " -> " +
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
                ast.type = 'Bool'
            else:
                print( 'ERROR: or clauses without bool type' )

    elif ast.name == 'boolTermList':
        if len(ast) == 1:
            ast.type = ast[0].type
        else:
            if isBool(asts(ast)):
                ast.type = 'Bool'
            else:
                print( 'ERROR TBD')

    elif ast.name == 'boolFactor':
        if ast.case(0):
            if isBool(ast[0]):
                ast.type = 'Bool'
            else: 
                ast.type = ast[0].type 
        elif ast.case(1):
            if isBool(ast[1]):
                ast.type = 'Bool'
            else:
                ast.type = ast[1].type
        else:
            ast.type = ast[1].type

    elif ast.name == 'simple-expression':
        if len(ast) == 1:
            ast.type = ast[0].type
        else:
            ast.type = 'Bool'

    elif ast.name == 'additive-expression':
        if len(ast) == 1:
            ast.type = ast[0].type
        else: 
            if ast[0].type == ast[2].type:
                ast.type =  ast[0].type
            else:
                print('ERROR: in additive-expression')

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
                ast.type = 'Int'
            else:
                ast.type = 'Int'
        #TODO: Else
        else:
            ast.type = 'Int'
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
                ast.type.append('Int')
    elif ast.name == 'var-declaration':
        for childname in ast[1]:
            if st.checkScope(childname):
                print("ERROR: " + childname + ' already defined in this scope')
                return False
            else:
                st.addSymbol(Var(childname, ast[0].baseType,
                    ast[0].dimensions, 'declared'))
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
    elif ast.name == 'args':
        ast.type = ast[0].type
    elif ast.name == 'arg-list':
        ast.type = tuple([x.type for x in asts(ast)])
    if ast.name == 'program':
        st.exitScope()
    return valid
