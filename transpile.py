from slr import SLRParser
from AST import AST
from AST import flattenLists
from AST import asts
from varClasses import *
from semantic import *
from typedef import *
import sys


promotions = {
    'Char': 'int',
    'Float': 'double',
    'Bool': 'int'
}
""" indent functions plus newline """

includes = ['stdarg','stdlib','stdio']
tab = ' '*4
def pref(td):
    return tab*(td)

def l0(s):
    return s + '\n'

def l1(s): 
    return pref(1) + s + '\n'

def l2(s):
    return pref(2) + s + '\n'

def line(s, indent):
    return pref(indent) + s + '\n'

def constructor(typ):
    name = typ.name
    ret = name + '* create' + name + '(' + name + 'Case type, ...)\n' 
    ret += l1(name + '* ret = malloc(sizeof('+ name +'));')
    ret += l1('va_list args;')
    ret += l1('va_start(args, type);')
    ifpref = 'if (type == '
    for i, item in enumerate(typ.types):
        print( item)
        if i == 0:
            ret += l1(ifpref + item + name + ') {')
            ret += pref(1) + '}'
            """ 
            ret->polar.r = (va_arg(args, double));
            """
        elif i < len(typ.types)-1:
            ret += l0(' else ' + ifpref + item + name + ') {')
            ret += pref(1) + '}'
        else:
            ret += l0(' else ' + ifpref + item + name + ') {')
            ret += pref(1) + '}\n'

    ret += pref(1) + 'va_end(args);\n'
    ret += pref(1) + 'return ret;\n}'
    return ret

def inc(string):
    return '#incude<' + string + '.h>'


# Final statement or return statement

# td short for tabDepth
def genC(ast, st, td):
    ret = ''
    if not isinstance(ast, AST):
        return ''
    name = ast.name
    if name == 'program':
        st.enterScope()

    if  name == 'productType':
        td+=1

    if name == 'var-declaration':
        for childname in ast[1]:
            st.addSymbol(Var(childname, ast[0].baseType + ast[0].brackets,0))
    elif name == 'assignment':
        for childname, value, typ in zip(ast[0],ast[2], ast.type):
            if not st.checkScope(name):
                ret += typ + ' ' + childname + ' = ' + value + ';\n'
                st.addSymbol(Var(childname, typ,0))
            else:
                ret += childname + ' = ' + value + ';\n'
    elif name == 'fun-declaration':
        td += 1

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
        td += 1
    if name == 'compound-stmt':
        td += 1


    """ top down above """
    for child in ast:
        ret += genC(child, st, td)
    """ bottom up below """

    if name == 'anonymous-function':
        ast.cstr = ast[2].cstr
    elif name == 'function-body':
        ast.cstr = ast[1].cstr + ast[2].cstr
    elif name == 'compound-stmt':
        ast.cstr = ast[1].cstr + ast[2].cstr
    elif name == 'local-declarations-list':
        ast.cstr = ((tab*td)+"\n").join([x.cstr for x in ast])
    elif name == 'iteration-stmt':
        if ast.case(0):
            ast.cstr = (tab*(td-1))
            ast.cstr += 'while ' + ast[2].cstr + ' {\n' 
            ast.cstr += ast[5].cstr
            ast.cstr += '\n' + (tab*(td-1)) + '}\n'
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
        #ret += tab*td + 'return ' + ast[0].cstr + ';\n'

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
        ast.type = ast[0].type
    elif name == 'arg-list':
        ast.cstr = ','.join([x.cstr for x in asts(ast)])
        ast.type = tuple([x.type for x in asts(ast)])
    elif name == 'statement-list':
        ast.cstr = '\n'.join([x.cstr for x in ast])
    elif name == 'statement':
        ast.cstr = ast[0].cstr
    elif name == 'expression-stmt':
        ast.cstr = (tab*td) +ast[0].cstr + ';'
    elif name == 'expressionList':
        if ast[-1].name == 'other-selection-stmt':
            resolved = ' = '.join([x.cstr + '' for x in asts(ast[:-1])])
            ast.cstr = ast[-1].cstr.replace('selectionResolution', resolved + ' =' )
        elif len(ast) > 1:
            ast.cstr = ' = '.join([x.cstr for x in asts(ast)])
        else:
            ast.cstr = ast[0].cstr
            # 
    elif name == 'var-declaration':
        ast.cstr = '' 
        for childname in ast[1]:
            ast.cstr += tab*td
            ast.cstr += st.findSymbol(childname).type + ' ' + childname
            ast.cstr += ';\n'
    elif name == 'declaration':
        ast.cstr = ast[0].cstr
    elif name == 'dataDeclaration':
        ast.cstr = ast[0].cstr
    elif name == 'constructor':
        typeclass = st.findSymbol(ast[0])
        ast.cstr = '//construct ' + typeclass.name + ':' + typeclass.signatures[ast[2].type] + '\n'


    elif name == 'productType':
        ast.cstr = 'typedef struct '+ast[1].lower()+' {\n'
        ast.cstr += ast[4].cstr
        ast.cstr += '} ' + ast[1] + ';\n'
        st.addSymbol(Product(ast,st))
    elif name == 'memberList':
        ast.cstr = ''.join([x.cstr for x in ast])
    elif name == 'sumType':
        # enum of cases/types for tagged union
        typeName = ast[1]
        typeList = [x for x in ast[3] if x != '|']
        ast.cstr = 'typedef enum ' + typeName.lower() + 'case'
        ast.cstr += ' {\n'
        ast.cstr += tab*(td+1) +','.join([x + typeName for x in typeList])
        ast.cstr += '\n} ' + typeName + 'Case;\n\n' 
        #TODO: 
        ast.cstr += 'typedef struct {\n'
        #ast.cstr += tab*(td+1) + 'enum pointcase case;\n'
        ast.cstr += pref(td+1) + typeName + 'Case type;\n'
        ast.cstr += tab*(td+1) + 'union {\n'
        st.addSymbol(Sum(ast,st))
        for innerTypeName in typeList:
            ast.cstr += pref(td+2)
            ast.cstr += innerTypeName + ' ' + innerTypeName.lower()
            ast.cstr += ';\n'

        ast.cstr += (tab*(td+1)) +'};\n'
        ast.cstr += (tab*td) + '} ' + typeName + ';\n\n' 
        ast.cstr += constructor(st.findSymbol(ast[1]))

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
                ast.cstr = tab*td + 'if '+ child.cstr
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
            ast.cstr = '{\n' + tab*td + ast[3].cstr.replace('\n','\n'+(tab))
            ast.cstr += '\n' + tab*(td) +'}'
        else:
            if ast.selectionResolution != 'return':
                ast.cstr += tab*(td+1)
                ast.cstr += ast[3].cstr + ';\n'
            else:
                if ast[3].name != 'other-selection-stmt':
                    ast.cstr += tab*(td+1)
                    ast.cstr += ast[3].cstr
            ast.cstr += tab*(td) + '}' 

    elif name == 'clause':
        ast.cstr = ast[2].cstr + ' {\n'
        if ast[5].name == 'final-stmt' and ast[5][0].name == 'other-selection-stmt':
            ast.cstr += tab*td + ast[5].cstr.replace('\n','\n'+(tab))
            ast.cstr += '\n' + tab*(td) +'}'
        else:
            if ast.selectionResolution != 'return':
                ast.cstr += tab*(td+1)
                ast.cstr += ast[5].cstr
                ast.cstr += ';\n'
            else:
                if ast[5].name != 'other-selection-stmt':
                    ast.cstr += tab*(td+1)
                    ast.cstr += ast[5].cstr
            ast.cstr += tab*(td) + '}' 

    elif name == 'fun-declaration':
        ast.cstr  = '\n' + ast.returnType.lower().replace('[]','*') + ' ' + ast[0][0] + str(Function(ast[2]).params) + ' {\n'
        ast.cstr += ast[2].cstr
        ast.cstr += '\n}\n'
        td -= 1
    
    elif name == 'declaration-list':
        ast.cstr = '\n'.join([x.cstr for x in ast])
    elif name == 'program':
        ast.cstr = '\n'.join([inc(x) for x in includes]) + '\n'
        st.exitScope()
        return ast.cstr + ast[0].cstr

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


