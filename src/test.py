import sys
from ctypes import CFUNCTYPE, c_int64
from slr import SLRParser
from AST import asts, AST, flattenLists
from varClasses import NamedType, FunType
from semantic import errorCheck
from symTable import SymbolTable, NamedSymbolTable
from llvmgen import create_llvm_types, codegen, module, create_execution_engine, compile_ir

from llvmlite import ir, binding


def test_int(engine):
    t_fun = CFUNCTYPE(c_int64, c_int64, c_int64)
    add = t_fun(engine.get_function_address('global.fun1'))
    sub = t_fun(engine.get_function_address('global.fun2'))
    mul = t_fun(engine.get_function_address('global.fun3'))
    div = t_fun(engine.get_function_address('global.fun4'))

    assert(add(3,4) == 3+4)
    assert(sub(3,4) == 3-4)
    assert(mul(3,4) == 3*4)
    assert(div(3,4) == 3//4)
    print('test_int passed')


def test_composition(engine):
    t_fun = CFUNCTYPE(c_int64, c_int64, c_int64)
    comp = t_fun(engine.get_function_address('global.fun5'))
    # this is not a hard check on x86 division
    assert(comp(1, 1) == (((1 + 1) * (1 - 1 ) // 1)))
    print('test_composition passed')

def test_factorial(engine):
    t_fun = CFUNCTYPE(c_int64, c_int64)
    fact = t_fun(engine.get_function_address('global.fun1'))
    assert(fact(1) == 1)
    assert(fact(5) == 120)
    assert(fact(7) == fact(5) * 6 * 7)
    print('test_factorial passed')

def test_struct(engine):
    pass

def test_guards(engine):
    t_fun = CFUNCTYPE(c_int64, c_int64, c_int64)
    eq = t_fun(engine.get_function_address('global.fun1'))
    assert(eq(1,1) == 1)
    assert(eq(1,2) == 0)

    cmp = t_fun(engine.get_function_address('global.fun2'))
    assert(cmp(2,1) == 1)
    assert(cmp(1,2) == -1)
    assert(cmp(1,1) == 0)
    print('test_guards passed')


test_inputs = {
    'test_int': test_int,
    'test_composition': test_composition,
    'test_guards': test_guards,
    'test_factorial': test_factorial,
}

def run_tests():
    for name in test_inputs:
        parser = SLRParser("new_grammar.txt", '../testInputs/' + name + '.txt')
        syn_tree = parser.parse()[0]
        syn_tree.genCases(parser.grammar)

        sym_table = SymbolTable()
        named_sym_table = NamedSymbolTable()

        valid = errorCheck(syn_tree,
                           sym_table,
                           named_sym_table,
                           parser.lexer.infileLines)


        llvm_custom_types = create_llvm_types(named_sym_table)
        module = ir.Module(name = name)
        generated_ir = codegen(syn_tree, named_sym_table, {
            'mod': module,
            'llvm_custom_types': llvm_custom_types
        })
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()  # yes, even this one
        binding.load_library_permanently('../runtime.so')

        binding.parse_assembly(str(module), None)
        engine = create_execution_engine()
        mod = compile_ir(engine, str(module))
        test_inputs[name](engine)


run_tests()
