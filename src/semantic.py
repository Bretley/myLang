import sys
from slr import *
from AST import asts, AST
from varClasses import Var, NamedType, FunType, ProductType
from symTable import SymbolTable, NamedSymbolTable, FuncInfo, UF, UFVar
from defaults import isDefault



def err(msg):
    print(msg)
    sys.exit(-1)

def err_if(cond, msg):
    if cond:
        err(msg)

def single_tuple(t):
    return t if isinstance(t, tuple) else (t,)

def param_type_from_tuple(t):
    if len(t) == 2:
        arg, to = t
        return FunType(arg, to)
    else:
        return FunType(t[0], param_type_from_tuple(t[1:]))


t_int = NamedType('Int')
t_float = NamedType('Float')
t_bool = NamedType('Bool')
t_unit = NamedType('non')

defaults = {
    'Int': t_int,
    'Float': t_float,
    'Bool': t_bool,
}


def check_translation_unit(ast, st, nst, fileLines):
    definitions = ast[0]
    st.enterScope()
    rec(definitions, st, nst, fileLines)
    nst.setScope({**nst.currentScope, **st.exitScope()})
    nst.exitScope()



def check_definitions(ast, st, nst, lines):
    if ast.case(0):  # definitions definition
        definitions, definition = ast.children
        rec(definitions, st, nst, lines)
        rec(definition, st, nst, lines)

    elif ast.case(1):
        definitions, = ast
        rec(definitions, st, nst, lines)

    else:
        err('fallthrough error in check_definitions')


def check_definition(ast, st, nst, lines):
    if ast.case(0):  # type_definition
        rec(ast[0], st, nst, lines)

    elif ast.case(1):  # declaration
        declaration, = ast
        rec(declaration, st, nst, lines)
        ast.type = declaration.type

    else:
        err('fallthrough error in check_definition')


def check_package(ast, st, nst, lines):
    pass


def check_imports(ast, st, nst, lines):
    pass


def check_type_definition(ast, st, nst, lines):
    rec(ast[0], st, nst, lines)


def check_assign_op(ast, st, nst, lines):
    pass


def check_declaration(ast, st, nst, lines):
    # var_declaration or fun_declaration
    declaration, = ast
    rec(declaration, st, nst, lines)
    ast.type = declaration.type


def check_fun_declaration(ast, st, nst, lines):
    _, ids, _, fun = ast
    t_unknown = FunType((NamedType('?'),), (NamedType('?'),))

    rec(ids, st, nst, lines)
    if (len(ids.names) > 1):
        err('error in check_fun_declaration, multiple ids')
    st.addSymbol(Var(ids.names[0], t_unknown, 0, None))
    rec(fun, st, nst, lines)
    st.addSymbol(Var(ids.names[0], fun.type, 0, None))


def check_space_sep_ID(ast, st, nst, lines):
    ast.names = ()
    if ast.case(0):  # space_sep_ID ID
        space_sep_id, _id = ast
        rec(space_sep_id, st, nst, lines)
        rec(_id, st, nst, lines)
        ast.names = space_sep_id.names + (_id[0],)

    elif ast.case(1):  # ID
        _id, = ast
        ast.names = (_id[0],)

    else:
        err('fallthrough error in check_space_sep_ID')


def check_var_declaration(ast, st, nst, lines):
    pass


def check_typeBarSeparated(ast, st, nst, lines):
    pass


def check_sumType(ast, st, nst, lines):
    pass


def check_product_type(ast, st, nst, lines):
    _, t_name, _, _, members, _ = ast
    t_name = t_name[0]
    nst.addScope(t_name, {})
    nst.enterScope(t_name)
    st.enterScope()

    nst.types[t_name] = NamedType('LL')
    rec(members, st, nst, lines)
    nst.types[t_name] = ProductType(members.names, members.type)

    print('---')
    print(members.names)
    print(nst.types[t_name].members)
    nst.setScope(st.exitScope())
    nst.exitScope()


def check_product_members(ast, st, nst, lines):
    if ast.case(0):  # product_members ,  product_member
        members, _, member = ast
        rec(members, st, nst, lines)
        rec(member, st, nst, lines)
        ast.names = members.names + member.names
        ast.type = members.type + single_tuple(member.type)

    if ast.case(1):  # product_member
        member, = ast
        rec(member, st, nst, lines)
        ast.names = member.names
        ast.type = member.type


def check_product_member(ast, st, nst, lines):
    typ, space_sep_id = ast
    rec(typ, st, nst, lines)
    rec(space_sep_id, st, nst, lines)
    ast.names = space_sep_id.names
    if typ[0] in defaults:
        ast.type = (defaults[typ[0]],) * len(ast.names)
    else:
        ast.type = (nst.types[typ[0]],) * len(ast.names)



def check_CONSTANT(ast, st, nst, lines):
    ast.type = defaults['Int']
    rec(ast[-1], st, nst, lines)
    # TODO: fix with caseNum
    if len(ast) == 1:  # NUM
        ast.literal_value = ast[-1].literal_value
    elif len(ast) == 2:  # - NUM
        ast.literal_value = - ast[-1].literal_value


def check_NUM(ast, st, nst, lines):
    ast.literal_value = int(ast[0])


def check_basic_expr(ast, st, nst, lines):
    if ast.case(0):  # ID
        _id, = ast
        rec(_id, st, nst, lines)
        ast.type = _id.type
    elif ast.case(1):  # CONSTANT
        const, = ast
        rec(const, st, nst, lines)
        ast.type = const.type
    elif ast.case(2):  # ( expr )
        _, expr, _ = ast
        rec(expr, st, nst, lines)
        ast.type = expr.type
    elif ast.case(3):  # constructor
        rec(ast[0], st, nst, lines)
        ast.type = ast[0].type
    elif ast.case(4):
        ast.type = t_unit
        ast.literalValue = 0

def check_constructor(ast, st, nst, lines):
    typ, _, args, _ = ast
    rec(typ, st, nst, lines)
    rec(args, st, nst, lines)
    print('-------------')
    print(args)
    print(typ)
    print(args.type)
    print(typ.type)
    print(typ)
    if args.type != typ.type:
        print(args.type)
        print(typ.type)
        err('Invalid constructor args in check_constructor')
    ast.type = NamedType(typ[0])


def check_anonymous_function(ast, st, nst, lines):
    scope_name = nst.path[-1] + '.fun' + str(st.next_fun())
    ast.fname = scope_name
    nst.addScope(scope_name, {})
    nst.enterScope(scope_name)
    st.enterScope()
    params, _, body = ast
    rec(params, st, nst, lines)
    for name, _type in zip(params.names, params.type):
        st.addSymbol(Var(name, _type, 0, None))
    rec(body, st, nst, lines)
    ast.type = param_type_from_tuple(params.type + (body.type,))
    ast.type = FunType(params.type, body.type)
    nst.setScope({**nst.currentScope, **st.exitScope()})
    nst.exitScope()


def check_params(ast, st, nst, lines):
    if ast.case(0):  # non
        ast.type = None
        ast.names = ()
    elif ast.case(1):  # param_comma_sep
        param_comma_sep, = ast
        rec(param_comma_sep, st, nst, lines)
        ast.type = param_comma_sep.type
        ast.names = param_comma_sep.names
    else:
        err('fallthrough error in check_params')


def check_param_comma_sep(ast, st, nst, lines):
    if ast.case(0):  # param_comma_sep , TYPE , space_sep_ID
        param_comma_sep, _, _type, space_sep_id = ast
        rec(param_comma_sep, st, nst, lines)
        rec(_type, st, nst, lines)
        rec(space_sep_id, st, nst, lines)
        ast.names = param_comma_sep.names + space_sep_id.names
        ast.type = param_comma_sep.type + tuple(_type.type for x in space_sep_id.names)
        for name, _type in zip(ast.names, ast.type):
            st.addSymbol(Var(name, _type, 0, None))

    elif ast.case(1):  # TYPE space_sep_ID
        _type, space_sep_id = ast
        rec(_type, st, nst, lines)
        rec(space_sep_id, st, nst, lines)
        ast.names = space_sep_id.names
        if _type[0] in defaults:
            ast.type = tuple(_type.type for x in ast.names)
        else:
            ast.type = _type[0],
    else:
        err('fallthrough error in check_param_comma_sep')


def check_func_body(ast, st, nst, lines):
    _, statement_list, final_stmt, _ = ast
    rec(statement_list, st, nst, lines)
    rec(final_stmt, st, nst, lines)
    if final_stmt.type is None:
        err('error in check_func_body: no final-stmt type')
    ast.type = final_stmt.type



def check_final_stmt(ast, st, nst, lines):
    # func_expr or guards
    rec(ast[0], st, nst, lines)
    ast.type = ast[0].type


def check_guards(ast, st, nst, lines):
    clause_list, final_clause = ast
    rec(clause_list, st, nst, lines)
    rec(final_clause, st, nst, lines)
    if clause_list.type != final_clause.type:
        print(clause_list.type)
        print(final_clause.type)
        err('final clause and clause list do not have same type')
    ast.type = ast[0].type


def check_clause_list(ast, st, nst, lines):
    if ast.case(0):  # clause_list clause
        clause_list, clause = ast
        rec(clause_list, st, nst, lines)
        rec(clause, st, nst, lines)
        if clause_list.type != clause.type:
            err('clauselist type not equal to clause type')
        ast.type = clause.type
    elif ast.case(1):  # clause
        rec(ast[0], st, nst, lines)
        ast.type = ast[0].type


def check_clause(ast, st, nst, lines):
    _, cond, _, ret = ast
    rec(cond, st, nst, lines)
    rec(ret, st, nst, lines)
    if cond.type != (defaults['Bool'],):
        err('bool clause type error')
    ast.type = ret.type


def check_final_clause(ast, st, nst, lines):
    _, _, _, ret = ast
    rec(ret, st, nst, lines)
    ast.type = ret.type

def check_post_expr(ast, st, nst, lines):
    if ast.case(0):  # basic_expr
        rec(ast[0], st, nst, lines)
        ast.type = ast[0].type
    elif ast.case(1):
        err('error in post expression, indexing and calling not supported yet')
    elif ast.case(2):  # post_expr ( arg_expr_list )
        post_expr, _, arg_expr_list, _ = ast
        rec(post_expr, st, nst, lines)
        rec(arg_expr_list, st, nst, lines)
        if post_expr.type.args != arg_expr_list.type:
            err('error in check_post_expr: call had invalid args types')
        ast.type = post_expr.type.to
    elif ast.case(3):  # post_expr . ID
        print('-------------------')
        post_expr, _, _id = ast
        rec(post_expr, st, nst, lines)
        print(post_expr.type)
        print(_id[0])
        print(nst.types)
        print(post_expr)
        print(_id[0])
        print(nst.types[post_expr.type.name].members)
        if _id[0] in nst.types[post_expr.type.name].members:
            members = nst.types[post_expr.type.name].members
            ast.type = members[_id[0]][1]
    else:
        err('fallthrough in check_post_expr')


def check_arg_expr_list(ast, st, nst, lines):
    if ast.case(0):  # empty
        ast.type = ()
    elif ast.case(1):  # assign_expr
        assign_expr, = ast
        rec(assign_expr, st, nst, lines)
        if isinstance(assign_expr.type, tuple):
            ast.type = assign_expr.type
        else:
            ast.type = assign_expr.type,
    elif ast.case(2):  # arg_expr_list , assign_expr
        arg_expr_list, _, assign_expr = ast
        rec(arg_expr_list, st, nst, lines)
        rec(assign_expr, st, nst, lines)
        ast.type = arg_expr_list.type + single_tuple(assign_expr.type)
    elif ast.case(3):  # func_expr
        func_expr, = ast
        rec(func_expr, st, nst, lines)
        ast.type = func_expr.type
    else:
        err('fallthrough in check_arg_expr_list')


def check_unary_expr(ast, st, nst, lines):
    rec(ast[0], st, nst, lines)
    ast.type = ast[0].type


def check_mult_expr(ast, st, nst, lines):
    if ast.case(0):  # unary_Expr
        unary_expr, = ast
        rec(unary_expr, st, nst, lines)
        ast.type = unary_expr.type
    elif ast.case(1) or ast.case(2):
        # mult_expr MULT_OP unary_expr
        mult_op, _, unary_expr = ast
        rec(mult_op, st, nst, lines)
        rec(unary_expr, st, nst, lines)
        c = ast
        while c.parent is not None:
            c = c.parent
        if single_tuple(mult_op.type) != single_tuple(unary_expr.type):
            err('error in check_mult_expr, mult_op must have same types')
        ast.type = unary_expr.type
    else:
        err('fallthrough in check_mult_expr')




def check_add_expr(ast, st, nst, lines):
    if ast.case(0):  # add_expr
        add_expr, = ast
        rec(add_expr, st, nst, lines)
        ast.type = add_expr.type
    elif ast.case(1) or ast.case(2):
        # add_expr ADD_OP mult_expr
        add_expr, _, unary_expr = ast
        rec(add_expr, st, nst, lines)
        rec(unary_expr, st, nst, lines)
        # TODO: verify addition types
        if add_expr.type != unary_expr.type:
            err('error in add_expr: add does not take two different types')
        ast.type = add_expr.type
    else:
        err('fallthrough in check_add_expr')


def check_shift_expr(ast, st, nst, lines):
    rec(ast[0], st, nst, lines)
    ast.type = ast[0].type


def check_relation_expr(ast, st, nst, lines):
    if ast.case(0):  # shift_expr
        shift_expr, = ast
        rec(shift_expr, st, nst, lines)
        ast.type = shift_expr.type
    elif ast.case(1) or ast.case(2) or ast.case(3) or ast.case(4):
        # relation_expr REL_OP shift_expr
        relation_expr, _, shift_expr = ast
        # TODO: check that types match
        rec(relation_expr, st, nst, lines)
        rec(shift_expr, st, nst, lines)
        ast.type = t_bool

    else:
        err('fallthroufh in check_relation_expr')


def check_equal_expr(ast, st, nst, lines):
    if ast.case(0):  # relation_expr
        relation_expr, = ast
        rec(relation_expr, st, nst, lines)
        ast.type = relation_expr.type
    elif ast.case(1) or ast.case(2):  # equal_expr EQ_OP relation_expr
        equal_expr, _, relation_expr = ast
        # TODO: Check that types are correct
        rec(equal_expr, st, nst, lines)
        rec(relation_expr, st, nst, lines)
        ast.type = t_bool
    else:
        err('fallthrough in check_equal_expr')


def check_bit_and_expr(ast, st, nst, lines):
    rec(ast[0], st, nst, lines)
    ast.type = ast[0].type


def check_bit_xor_expr(ast, st, nst, lines):
    rec(ast[0], st, nst, lines)
    ast.type = ast[0].type


def check_bit_or_expr(ast, st, nst, lines):
    rec(ast[0], st, nst, lines)
    ast.type = ast[0].type


def check_logic_and_expr(ast, st, nst, lines):
    if ast.case(0):  # bit_or_expr
        bit_or_expr, = ast[0]
        rec(bit_or_expr, st, nst, lines)
        ast.type = bit_or_expr.type
    elif ast.case(1):  # logic_and_expr ^ bit_or_expr
        logic_and_expr, _, bit_or_expr = ast
        # TODO: check the types match
        rec(logic_and_expr, st, nst, lines)
        rec(bit_or_expr, st, nst, lines)
        ast.type = t_bool
    else:
        err('fallthrough in logic_and_expr')


def check_logic_or_expr(ast, st, nst, lines):
    if ast.case(0):  # logic_and_expr
        and_expr, = ast
        rec(and_expr, st, nst, lines)
        ast.type = and_expr.type
    elif ast.case(1):  # logic_or_expr v logic_and_expr
        or_expr, _, and_expr = ast
        # TODO: check that the types are correct
        rec(or_expr, st, nst, lines)
        rec(and_expr, st, nst, lines)
        ast.type = t_bool
    else:
        err('fallthrough in check_logic_or_expr')


def check_assign_expr(ast, st, nst, lines):
    if ast.case(0):  # assign_expr = logic_or_expr
        assign_expr, _, logic_or_expr = ast
        rec(assign_expr, st, nst, lines)
        # TODO: check that the types match up
        rec(logic_or_expr, st, nst, lines)
        ast.type = logic_or_expr.type
    elif ast.case(1):  # logic_or_expr
        logic_or_expr, = ast
        rec(logic_or_expr, st, nst, lines)
        ast.type = logic_or_expr.type
    else:
        err('fallthrough in check_assign_expr')


def check_expression(ast, st, nst, lines):
    if ast.case(0):  # expression , assign_expr
        expr, _, assign_expr = ast
        rec(expr, st, nst, lines)
        rec(assign_expr, st, nst, lines)
        ast.type = expr.type + (assign_expr.type,)
    elif ast.case(1):  # assign_expr
        assign_expr, = ast
        rec(assign_expr, st, nst, lines)
        ast.type = assign_expr.type
        if not isinstance(ast.type, tuple):
            ast.type = (assign_expr.type,)
    else:
        err('fallthrough error in check_expression')
    pass



def check_func_expr(ast, st, nst, lines):
    rec(ast[0], st, nst, lines)
    ast.type = ast[0].type


def check_expression_stmt(ast, st, nst, fileLines):
    pass


def check_statement(ast, st, nst, fileLines):
    pass


def check_statement_list(ast, st, nst, fileLines):
    pass


def check_ID(ast, st, nst, lines):
    _id, = ast
    sym = st.findSymbol(_id)
    ast.type = None if sym is None else sym.type

def check_TYPE(ast, st, nst, lines):
    _typ, = ast
    if _typ in defaults:
        ast.type = defaults[_typ]
    elif _typ in nst.types:
        r = nst.types[_typ]
        if isinstance(r, NamedType):
            ast.type = r
        else:
            ast.type = nst.types[_typ].type
    else:
        print(nst.types)
        err('error in check_TYPE: ')


def rec(ast, st, nst, lines):
    checker[ast.name](ast, st, nst, lines)


checker = {
    'translation_unit': check_translation_unit,
    'package': check_package,
    'imports': check_imports,
    'definitions': check_definitions,
    'definition': check_definition,
    'type_definition': check_type_definition,
    'assign_op': check_assign_op,
    'declaration': check_declaration,
    'fun_declaration': check_fun_declaration,
    'space_sep_ID': check_space_sep_ID,
    'var_declaration': check_var_declaration,
    'typeBarSeparated': check_typeBarSeparated,
    'sumType': check_sumType,
    'CONSTANT': check_CONSTANT,
    'basic_expr': check_basic_expr,
    'constructor': check_constructor,
    'anonymous_function': check_anonymous_function,
    'params': check_params,
    'param_comma_sep': check_param_comma_sep,
    'func_body': check_func_body,
    'final_stmt': check_final_stmt,
    'guards': check_guards,
    'clause_list': check_clause_list,
    'clause': check_clause,
    'final_clause': check_final_clause,
    'post_expr': check_post_expr,
    'arg_expr_list': check_arg_expr_list,
    'unary_expr': check_unary_expr,
    'mult_expr': check_mult_expr,
    'add_expr': check_add_expr,
    'shift_expr': check_shift_expr,
    'relation_expr': check_relation_expr,
    'equal_expr': check_equal_expr,
    'bit_and_expr': check_bit_and_expr,
    'bit_xor_expr': check_bit_xor_expr,
    'bit_or_expr': check_bit_or_expr,
    'logic_and_expr': check_logic_and_expr,
    'logic_or_expr': check_logic_or_expr,
    'assign_expr': check_assign_expr,
    'expression': check_expression,
    'func_expr': check_func_expr,
    'expression_stmt': check_expression_stmt,
    'statement': check_statement,
    'statement_list': check_statement_list,
    'ID': check_ID,
    'TYPE': check_TYPE,
    'NUM': check_NUM,
    'product_type': check_product_type,
    'product_members': check_product_members,
    'product_member': check_product_member,
}

def errorCheck(ast, st, nst, lines, ):
    check_translation_unit(ast, st, nst, lines)

