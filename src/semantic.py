import sys
from slr import *
from AST import asts, AST
from varClasses import Var
from errors import Error
from typedef import Product, Sum
from symTable import *
from defaults import isDefault

e = Error(sys.argv[1])

OP_SIGNATURES = {
    'term': {
        ('Int', 'mulop', 'Int'): 'Int',
        ('Int',): 'Int'
    },
    'additive-expression': {
        ('Int', 'addop', 'Int'): 'Int',
        ('Int',): 'Int'
    },
    'simple-expression': {
        ('Int', 'relop', 'Int'): 'Bool',
        ('Int',): 'Int',
        ('Bool',): 'Bool'
    },
    'boolFactor': {
        ('Int',): 'Int',
        ('Bool',): 'Bool',
    }
}


def is_bool(*args):
    """Returns true if all items in args have type Bool
        Args:
            *args: List
                Either the first is a list, in which case it is evaluated,
                or every item in *args must have type Bool
        Returns:
            True if all items in args (or args[0]) have type 'Bool'
    """
    r = args[0] if isinstance(args[0], list) else args
    return all([x.type == 'Bool' for x in r])

def typeOf(ast):
    """Recursively marks ast and returns type
        Args:
            ast: AST
                ast to be evaluated
        Returns:
            type of top ast
    """
    if ast.type:
        return ast.type
    if ast.name in ['compound-stmt', 'final-stmt']:
        ast.type = typeOf(ast[0])  # type of final/compound
    elif ast.name == 'simple-expression' and len(ast.children) == 1:
        ast.type = typeOf(ast[0])
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

    # Make name and type synonymous for leaves
    if ast.name in ['addop', 'relop', 'mulop']:
        ast.type = ast.name

    if ast.name == 'program':
        st.enterScope()
    elif ast.name == 'productType':
        e.err_if(isDefault(ast[1]),
                 'Type definition error\ntype ' + ast[1] + ' already defined',
                 'Semantic', ast.lineNum-1)
        st.enterScope()
        namedST.addScope(ast[1], {})
        namedST.enterScope(ast[1])

    elif ast.name == 'fun-declaration':
        if len(ast[0].children) != 1:
            # TODO: Remove this from grammar?
            err( "only one name per function definition allowed")
            return False
        st.enterScope()
        namedST.addScope(ast[0][0], {})
        namedST.enterScope(ast[0][0])

    """ Top down above here """
    for child in ast:
        valid &= errorCheck(child, st, namedST, fileLines)
        if not valid:
            return False
    """ Bottom up below here """

    for x in asts(ast):
        ast.hoists += x.hoists

    if ast.name == 'params':
        ast.type = ast[0].type
        ast.names = ast[0].names if isinstance(ast[0], AST) else None
        for name in ast.names:
            st.findSymbol(name).info = ('param', 1)
            print(st.findSymbol(name))
        print(ast.names)

    if ast.name == 'param-list':
        ast.type = []
        ast.names = []
        for child in asts(ast):
            ast.type += child.type
            ast.names += child.names
        print(st.stack[-1])

    if ast.name == 'param':
        ast.type = ast[0].type
        ast.names = ast[0].names

    elif ast.name == 'productType':
        namedST.setScope(st.exitScope())
        namedST.exitScope()
        st.addSymbol(Product(ast, st))
    elif ast.name == 'sumType':
        st.addSymbol(Sum(ast,st))
    elif ast.name == 'constructor':
        symbol = st.findSymbol(ast[0])
        e.err_if(symbol is None,
                 'Constructor error\n' + 'type ' + ast[0] + ' not defined' ,
                 'Semantic',
                 ast.lineNum)

        e.err_if(ast[2].type != symbol.signatures,
                 'Constructor error\nNo valid constructor of type: ' +
                 str(ast[2].type) + '\nfound for type ' + symbol.name + '\n',
                 'Semantic', ast.lineNum)
        ast.type = ast[0]

    elif ast.name == 'namedParam':
        ast.type = []
        ast.names = ast[1]
        for i, name in enumerate(ast[1]):
            e.err_if(st.checkScope(name),
                     'Parameter Error:\n' + 'variable ' + name + ' already defined',
                     'Semantic', ast.lineNum)
            v = Var(name, ast[0].baseType, ast[0].dimensions, 'param')
            st.addSymbol(v)
            ast.type += [ast[0].baseType]

    elif ast.name == 'destructuredParam':
        ast.names = []
        e.err_if(ast[0].dimensions > 0,
                 'Type specifier has dimension higher than 0',
                 'Semantic', ast.lineNum)

        e.err_if(isDefault(ast[0][0]),
                 'Trying to destructure a default param',
                 'Semantic', ast.lineNum)

        typ = st.findSymbol(ast[0][0])
        e.err_if(typ is None,
                 'Type not defined before use in destructure',
                 'Semantic', ast.lineNum)

        e.err_if(not isinstance(typ, Product),
                 'Type used in destructure is not a product',
                 'Semantic', ast.lineNum)

        for name in ast[2]:
            var = typ.get(name)
            #TODO: Make these better pls
            e.err_if(var is None,
                     'Name within destructure not a member of the enclosing Type',
                     'Semantic', ast.lineNum)

            e.err_if(st.checkScope(var.name),
                     'Param ' + var.name + ' already defined',
                     'Semantic', ast.lineNum)

            v = Var(var.name, var.type, var.dimensions, 'destructuredParam')
            st.addSymbol(v)
        ast.type = [ast[0][0]]

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
        ast.type = ast[-1].type  # Always the type of farthest rhs
        # TODO: give this a look over
        for varName in asts(ast)[:-1]:
            var = st.findSymbol(varName[0])
            if var is not None:
                e.err_if(var.type != ast.type,
                         'Attempting to assign expression of type: ' +
                         str(ast.type) + ' -> ' + str(var.type),
                         'Semantic', ast.lineNum)

            st.addSymbol(Var(varName[0], ast.type, 0, 'hoisted'))
            # TODO: deal with multi dimensions
            ast.hoists.append(st.findSymbol(varName[0]))

    elif ast.name == 'boolExprList':
        if len(ast) == 1:
            ast.type = ast[0].type
        elif is_bool(asts(ast)):
            ast.type = 'Bool'
        else:
            print('ERROR: or clauses without bool type')

    elif ast.name == 'boolTermList':
        if len(ast) == 1:
            ast.type = ast[0].type
        elif is_bool(asts(ast)):
            ast.type = 'Bool'
        else:
            print('ERROR TBD')

    elif ast.name == 'boolFactor':
        signature = tuple(x.type for x in asts(ast))
        e.err_if(signature not in OP_SIGNATURES['boolFactor'],
                 'Error in simple-expression, invalid signature',
                 'Semantic', ast.lineNum)
        ast.type = OP_SIGNATURES['boolFactor'][signature]

    elif ast.name == 'simple-expression':
        signature = tuple(x.type for x in asts(ast))
        e.err_if(signature not in OP_SIGNATURES['simple-expression'],
                 'Error in simple-expression, invalid signature',
                 'Semantic', ast.lineNum)
        ast.type = OP_SIGNATURES['simple-expression'][signature]

    elif ast.name == 'additive-expression':
        signature = tuple(x.type for x in asts(ast))
        e.err_if(signature not in OP_SIGNATURES['additive-expression'],
                 'Error in additive-expression, invalid signature',
                 'Semantic', ast.lineNum)
        ast.type = OP_SIGNATURES['additive-expression'][signature]

    elif ast.name == 'term':
        signature = tuple(x.type for x in asts(ast))
        e.err_if(signature not in OP_SIGNATURES['term'],
                 'Error in term, invalid signature',
                 'Semantic', ast.lineNum)
        ast.type = OP_SIGNATURES['term'][signature]

    elif ast.name == 'factor':
        # TODO: fix fix fix
        if ast.case(0):
            ast.type = ast[1].type
        elif ast.case(1):
            if isinstance(ast[0], AST) and ast[0].name == 'var':
                e.err_if(not st.checkScope(ast[0][0]),
                          'Error: ' + str(ast[0][0]) + ' undefined in local scope',
                         'Semantic', ast.lineNum)
                var = st.findSymbol(ast[0][0])
                ast.type = var.type + '[]'*(var.dimensions - len(ast[0][1]))
            elif not isinstance(ast[0], AST):
                ast.type = 'Int'
            else:
                ast.type = 'Int'
        elif ast.case(2):
            # TODO: Check type signature of call
            ast.type = 'Int'
        else:
            ast.type = 'Int'

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
        for child in ast[1]:
            e.err_if(st.checkScope(child),
                     child + ' already defined in this scope',
                     'Semantic', ast.lineNum)

            v = Var(child, ast[0].baseType, ast[0].dimensions, 'declared')
            st.addSymbol(v)

    elif ast.name == 'bracket-group':
        if len(ast.children) == 2:
            ast.length = ''
        else:
            ast.length = ast[1]
        ast.singlet = ''.join(ast.children)
    elif ast.name == 'type-specifier':
        ast.baseType = ast[0]
        ast.dimensions = len(ast[1].children)
        ast.brackets = ''.join([singlet.singlet for singlet in ast[1]])
    elif ast.name == 'args':
        ast.type = ast[0].type
    elif ast.name == 'arg-list':
        ast.type = tuple([x.type for x in asts(ast)])
    if ast.name == 'program':
        st.exitScope()
    return valid
