import sys
import ctypes
from slr import SLRParser
from AST import asts, AST, flattenLists
from varClasses import NamedType, FunType
from semantic import errorCheck
from symTable import SymbolTable, NamedSymbolTable

from llvmlite import ir, binding
from ctypes import CFUNCTYPE, c_double, c_int

import llvmlite

b = binding.create_context()

i64 = ir.IntType(64)
fp = ir.DoubleType()
boolean = ir.IntType(1)
unit = 'll_unit'

module = ir.Module(name='Default')
fnty = ir.FunctionType(ir.VoidType(), ())
ext_func = ir.Function(module, fnty, name='test')
fnty = ir.FunctionType(i64, (i64,))
runtime_my_malloc = ir.Function(module, fnty, name='My_Malloc')
fnty = ir.FunctionType(i64, (i64,))
runtime_print_int = ir.Function(module, fnty, name = 'Print_int')
t_data = binding.create_target_data('e-m:o-i64:64-f80:128-n8:16:32:64-S128')

def gen_unit(t):
    return t(None)

defaults = {
    NamedType('Int'): i64,
    NamedType('Float'): fp,
    NamedType('Bool'): boolean
}

def llvm_fun_type(ftype, nst, ctx):
    assert(isinstance(ftype, FunType))
    lltypes = ctx['llvm_custom_types']
    p_type, ret_type = ftype.args, ftype.to
    if isinstance(p_type, tuple):
        sig = []
        for x in p_type:
            if x in defaults:
                sig.append(defaults[x])
            else:
                #TODO: pointer to type
                sig.append(lltypes[x].as_pointer())
        p_type = tuple(sig)
    else:
        p_type = defaults[p_type],

    print('---')
    print(ret_type)
    print(ftype)
    if ret_type[0] in defaults:
        ret_type = defaults[ret_type[0]]
    elif ret_type[0] in nst.types:
        ret_type = ir.global_context.get_identified_type(ret_type[0]).as_pointer()
    print('---')
    print(ret_type)
    return ir.FunctionType(ret_type, p_type)


def guard_codegen(guards, final, nst, ctx, depth=0, endif=None):
    if not guards:
        codegen(final[3], nst, ctx)
        endif = ctx['builder'].append_basic_block('endif')
        return endif
    b = ctx['builder']
    current = guards[0]
    condition = codegen(current[2], nst, ctx)
    then_block = b.append_basic_block('if')
    else_block = b.append_basic_block('else')
    b.cbranch(condition, then_block, else_block)
    # generate true branch
    b.position_at_start(then_block)
    codegen(current[5], nst, ctx)
    # generate false branch
    b.position_at_start(else_block)
    endif = guard_codegen(guards[1:], final, nst, ctx, depth + 1, endif)
    if len(guards) == 1:
        b.position_at_end(else_block)
        b.branch(endif)
    b.position_at_end(then_block)
    b.branch(endif)
    return endif


def binop(ast: AST, nst: NamedSymbolTable, ctx=None):
    left = codegen(ast[0], nst, ctx)
    right = codegen(ast[2], nst, ctx)
    op = ast[1][0] if isinstance(ast[1], AST) else ast[1]
    return left, right, op


def conjunctive_bool(ast, nst, ctx):
    if len(ast) == 1:
        return codegen(ast[0], nst, ctx)
    else:
        l, r, op = binop(ast, nst, ctx)
        lhs = ctx['builder'].and_(l, r)
        if op == 'v':
            operation = ctx['builder'].or_
        elif op == '^':
            operation = ctx['builder'].and_
        else:
            operation = None
        for rhs in asts(ast)[2:]:
            rhs = codegen(rhs, nst, ctx)
            lhs = operation(lhs, rhs)
        return lhs


def gen_translation_unit(ast, nst, ctx):
    nst.enterScope('global')
    definitions, = ast
    return codegen(definitions, nst, ctx)


def gen_definitions(ast, nst, ctx):
    if ast.case(0):  # definitions definition
        definitions, definition = ast
        codegen(definitions, nst, ctx)
        codegen(definition, nst, ctx)
    elif ast.case(1):  # definition
        definition, = ast
        codegen(definition, nst, ctx)


def gen_definition(ast, nst, ctx):
    # type_definition or declaration
    if ast[0].name != 'type_definition':
        codegen(ast[0], nst, ctx)


def gen_declaration(ast, nst, ctx):
    codegen(ast[0], nst, ctx)


def gen_fun_declaration(ast, nst, ctx):
    _, space_sep_id, _, anonymous_fun = ast
    v = ir.GlobalVariable(
        ctx['mod'],
        llvm_fun_type(anonymous_fun.type, nst, ctx).as_pointer(),
        space_sep_id[0][0]
    )
    var_info = nst.currentScope[space_sep_id[0][0]]
    var_info.llvm_info = v
    fun = codegen(anonymous_fun, nst, ctx)
    v.initializer = fun


def gen_anonymous_function(ast, nst, ctx):
    params, _, body = ast
    fname = ast.fname
    nst.enterScope(fname)
    ftype = llvm_fun_type(ast.type, nst, ctx)
    print(ftype)
    func = ir.Function(ctx['mod'], ftype, name=fname)
    entry = func.append_basic_block('entry')
    for arg, name in zip(func.args, params.names):
        arg.name = name
        nst.currentScope[name].llvm_info = arg
    builder = ir.IRBuilder(entry)
    new_ctx = {'builder': builder, **ctx}
    codegen(params, nst, new_ctx)
    codegen(body, nst, new_ctx)
    nst.exitScope()
    return func


def gen_params(ast, nst, ctx):
    # TODO: other things
    ret = []
    for x in ast.type:
        if x in defaults:
            ret.append(defaults[x])
        else:
            ret.append(ctx['llvm_custom_types'][x])
    return tuple(ret)


def gen_func_body(ast, nst, ctx):
    _, statement_list, final_stmt, _ = ast
    # TODO: codegen of statement_list
    if ast.case(0):
        ctx['builder'].ret(codegen(final_stmt, nst, ctx))
    else:
        ctx['builder'].ret(i64(5))


def gen_final_stmt(ast, nst, ctx):
    # func_expr or guards
    return codegen(ast[0], nst, ctx)


def gen_func_expr(ast, nst, ctx):
    if ast.case(0): # anonymous_function
        pass
    elif ast.case(1):  # expression
        return codegen(ast[0], nst, ctx)


def gen_expression(ast, nst, ctx):
    if ast.case(0):  # expression , assign_expr
        expression, _, assign_expr = ast
        codegen(expression, nst, ctx)
        codegen(assign_expr, nst, ctx)
    elif ast.case(1):
        assign_expr, = ast
        return codegen(assign_expr, nst, ctx)


def gen_assign_expr(ast, nst, ctx):
    if ast.case(0):  # assign_expr = logic_or_expr
        pass
    elif ast.case(1):  # logic_expr
        logic_or_expr, = ast
        return codegen(logic_or_expr, nst, ctx)


def gen_logic_or_expr(ast, nst, ctx):
    return codegen(ast[0], nst, ctx)


def gen_logic_and_expr(ast, nst, ctx):
    return codegen(ast[0], nst, ctx)


def gen_bit_or_expr(ast, nst, ctx):
    return codegen(ast[0], nst, ctx)


def gen_bit_xor_expr(ast, nst, ctx):
    return codegen(ast[0], nst, ctx)


def gen_bit_and_expr(ast, nst, ctx):
    return codegen(ast[0], nst, ctx)


def gen_equal_expr(ast, nst, ctx):
    if ast.case(0):  # relation_expr
        relation_expr, = ast
        return codegen(relation_expr, nst, ctx)
    elif ast.case(1) or ast.case(2):
        equal_expr, cmp_op, relation_expr = ast
        return ctx['builder'].icmp_signed(
            cmp_op, codegen(equal_expr, nst, ctx),
            codegen(relation_expr, nst, ctx)
        )


def gen_relation_expr(ast, nst, ctx):
    if ast.case(0):  # shift_expr
        shift_expr, = ast
        return codegen(shift_expr, nst, ctx)
    elif ast.case(1) or ast.case(2) or ast.case(2) or ast.case(4):
        relation_expr, cmp_op, shift_expr = ast
        return ctx['builder'].icmp_signed(
            cmp_op, codegen(relation_expr, nst, ctx),
            codegen(shift_expr, nst, ctx)
        )


def gen_shift_expr(ast, nst, ctx):
    return codegen(ast[0], nst, ctx)


def gen_add_expr(ast, nst, ctx):
    if ast.case(0):  # mult_expr
        return codegen(ast[0], nst, ctx)
    lhs, op, rhs = ast
    op = ctx['builder'].add if op == '+' else ctx['builder'].sub
    lhs = codegen(lhs, nst, ctx)
    rhs = codegen(rhs, nst, ctx)
    return op(lhs, rhs)


def gen_mult_expr(ast, nst, ctx):
    if ast.case(0):  # unary_expr
        return codegen(ast[0], nst, ctx)
    lhs, op, rhs = ast
    op = ctx['builder'].mul if op == '*' else ctx['builder'].sdiv
    lhs = codegen(lhs, nst, ctx)
    rhs = codegen(rhs, nst, ctx)
    return op(lhs, rhs)


def gen_unary_expr(ast, nst, ctx):
    return codegen(ast[0], nst, ctx)


def gen_post_expr(ast, nst, ctx):
    if ast.case(0):
        return codegen(ast[0], nst, ctx)
    elif ast.case(1):
        print('??????')
    elif ast.case(2):  # post_expr ( arg_expr_list )
        post_expr, _ , arg_expr_list, _ = ast
        a = codegen(post_expr, nst, ctx)
        b = codegen(arg_expr_list, nst, ctx)
        return ctx['builder'].call(
            ctx['builder'].load(a), b
        )
    elif ast.case(3):  # post_expr [ arg_expr_list ]
        post_expr, _, _id = ast
        t_name = post_expr.type.name
        post_expr = codegen(post_expr, nst, ctx)
        index = nst.types[t_name].members[_id[0]][0]
        b = ctx['builder']
        a = b.load(post_expr)
        c = b.extract_value(a, index)
        print(c)
        return c

    else:
        print('not implemented yet, call or index')


def gen_basic_expr(ast, nst, ctx):
    if ast.case(0):  # ID
        if ast[0][0] in nst.currentScope:
            return nst.currentScope[ast[0][0]].llvm_info
        else:
            print(nst.tree['global'][ast[0][0]])
            print(nst.tree)
            return nst.tree['global'][ast[0][0]].llvm_info

    elif ast.case(1):  # CONSTANT
        return i64(ast[0].literal_value)
    elif ast.case(2):  # ( expression )
        pass
    elif ast.case(3):  # constructor
        return codegen(ast[0], nst, ctx)
    elif ast.case(4):
        return unit


def gen_constructor(ast, nst, ctx):
        typ, _, args, _ = ast
        lltypes = ctx['llvm_custom_types']
        args = codegen(args, nst, ctx)
        b = ctx['builder']
        #size = lltypes[ast.type].get_abi_size(t_data)
        t = ir.global_context.get_identified_type(ast.type.name)
        size = t.get_abi_size(t_data)
        ptr = b.inttoptr(
            b.call(runtime_my_malloc, (i64(size),)),
            t.as_pointer()
        )
        struct = b.load(ptr)
        print(args)
        for index, val in enumerate(args):
            if val == unit:
                val = gen_unit(t.elements[index])
            struct = b.insert_value(struct, val, index)

        b.store(struct, ptr)
        return ptr



def gen_arg_expr_list(ast, nst, ctx):
    if ast.case(0):  # empty
        return ()
    elif ast.case(1):  # assign_expr
        return codegen(ast[0], nst, ctx),
    elif ast.case(2):
        arg_expr_list, _, assign_expr = ast
        a = codegen(arg_expr_list, nst, ctx)
        b = codegen(assign_expr, nst, ctx),
        return a + b
    elif ast.case(3):  # func_expr
        return codegen(ast[0], nst, ctx),


def gen_guards(ast, nst, ctx):
    guard_ptr = ctx['builder'].alloca(defaults[ast.type[0]], name='.guard_ret')
    clause_list, final_clause = ast
    ret_val = gen_clause_list(clause_list, nst, ctx, final_clause, guard_ptr)
    return ctx['builder'].load(guard_ptr)


def gen_clause_list(ast, nst, ctx, final, guard_ptr, depth = 0):
    b = ctx['builder']
    if ast.case(0):  # clause_list clause
        clause_list, clause = ast
        _, cond, _, expr = clause

        true_block = b.append_basic_block('if')
        false_block = b.append_basic_block('else')
        end_guard = gen_clause_list(clause_list, nst, ctx, final, guard_ptr, depth+1)
        gen_cond = codegen(cond, nst, ctx)
        #print(gen_cond)
        b.cbranch(gen_cond, true_block, false_block)
        b.position_at_start(true_block)
        b.store(codegen(expr, nst, ctx), guard_ptr)
        b.branch(end_guard)
        b.position_at_start(false_block)
        if depth == 0:  # last one
            b.store(codegen(final[3], nst, ctx), guard_ptr)
            print(final[3])
            b.branch(end_guard)
            b.position_at_start(end_guard)
        return end_guard

    elif ast.case(1):  # clause
        # 'first' clause
        clause, = ast
        _, cond, _, expr = clause
        end_guard = b.append_basic_block('.guard_end')

        true_block = b.append_basic_block('if')
        false_block = b.append_basic_block('else')
        gen_cond = codegen(cond, nst, ctx)
        b.cbranch(gen_cond, true_block, false_block)
        # if (c1, v1)
        b.position_at_start(true_block)
        b.store(codegen(expr, nst, ctx), guard_ptr)
        b.branch(end_guard)
        # else (...rest)
        b.position_at_start(false_block)
        if depth == 0:  # last one
            b.store(codegen(final[3], nst, ctx), guard_ptr)
            b.branch(end_guard)
            b.position_at_start(end_guard)
        return end_guard


def codegen(ast, nst, ctx):
    return rec_dict[ast.name](ast, nst, ctx)


rec_dict = {
    'translation_unit': gen_translation_unit,
    'definitions': gen_definitions,
    'definition': gen_definition,
    'declaration': gen_declaration,
    'fun_declaration': gen_fun_declaration,
    'anonymous_function': gen_anonymous_function,
    'params': gen_params,
    'func_body': gen_func_body,
    'final_stmt': gen_final_stmt,
    'func_expr': gen_func_expr,
    'expression': gen_expression,
    'assign_expr': gen_assign_expr,
    'logic_or_expr': gen_logic_or_expr,
    'logic_and_expr': gen_logic_and_expr,
    'bit_or_expr': gen_bit_or_expr,
    'bit_xor_expr': gen_bit_xor_expr,
    'bit_and_expr': gen_bit_and_expr,
    'equal_expr': gen_equal_expr,
    'relation_expr': gen_relation_expr,
    'shift_expr': gen_shift_expr,
    'add_expr': gen_add_expr,
    'mult_expr': gen_mult_expr,
    'unary_expr': gen_unary_expr,
    'post_expr': gen_post_expr,
    'basic_expr': gen_basic_expr,
    'arg_expr_list': gen_arg_expr_list,
    'guards': gen_guards,
    'constructor': gen_constructor,
}

def create_llvm_types(nst,ctx):
    types = nst.types
    print(types)
    ret = {}
    for name in types:
        named_type = ctx.get_identified_type(name)
        elems = []
        for typ in types[name].type:
            if not isinstance(typ, NamedType):
                typ = NamedType(typ)
            if typ in defaults:
                elems.append(defaults[typ])
            else:
                elems.append(ctx.get_identified_type(typ.name).as_pointer())
        named_type.set_body(*tuple(elems))
    return ret


def create_execution_engine():
    """
    Create an ExecutionEngine suitable for JIT code generation on
    the host CPU.  The engine is reusable for an arbitrary number of
    modules.
    """
    # Create a target machine representing the host
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    # And an execution engine with an empty backing module
    backing_mod = binding.parse_assembly("")
    engine = binding.create_mcjit_compiler(backing_mod, target_machine)
    return engine


def compile_ir(engine, llvm_ir):
    """
    Compile the LLVM IR string with the given engine.
    The compiled module object is returned.
    """
    # Create a LLVM module object from the IR
    mod = binding.parse_assembly(llvm_ir)
    mod.verify()
    # Now add the module and make sure it is ready for execution
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    return mod





# iniitalized globals

# run
"""
parser = SLRParser("new_grammar.txt", sys.argv[1])
syn_tree = parser.parse()[0]
syn_tree.genCases(parser.grammar)

sym_table = SymbolTable()
named_sym_table = NamedSymbolTable()

valid = errorCheck(syn_tree,
                   sym_table,
                   named_sym_table,
                   parser.lexer.infileLines)


llvm_custom_types = create_llvm_types(named_sym_table)
generated_ir = codegen(syn_tree, named_sym_table, {
    'mod': module,
})
biding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()  # yes, even this one
binding.load_library_permanently('../runtime.so')
print(module)

binding.parse_assembly(str(module), None)
engine = create_execution_engine()
mod = compile_ir(engine, str(module))

func_ptr = engine.get_function_address('global.fun1')
createIntPair = CFUNCTYPE(c_int, c_int, c_int)(func_ptr)
a = (createIntPair(1, 2))
print(a)
func_ptr = engine.get_function_address('global.fun2')
createIntPair = CFUNCTYPE(c_int, c_int, c_int)(func_ptr)
a = (createIntPair(1, 2))
print(a)
func_ptr = engine.get_function_address('global.fun4')
t  = CFUNCTYPE(c_int, c_int)(func_ptr)
print(t(5))

a = 2
b = -2
print(add(c_int(3),c_int(3)))
print(div(c_int(a),c_int(b)))
print(mul(c_int(a),c_int(b)))
print(sub(c_int(a),c_int(b)))
print(add2(c_int(1),c_int(0)))
"""
