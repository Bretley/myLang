import sys
from ctypes import CFUNCTYPE, c_int64
from slr import SLRParser
from AST import asts, AST, flattenLists
from varClasses import NamedType, FunType
from semantic import errorCheck
from symTable import SymbolTable, NamedSymbolTable
from llvmgen import create_llvm_types, codegen, module, create_execution_engine, compile_ir
from llvmlite import ir, binding

name = sys.argv[1]
parser = SLRParser("new_grammar.txt", '../testInputs/' + name)
syn_tree = parser.parse()[0]
syn_tree.genCases(parser.grammar)

sym_table = SymbolTable()
named_sym_table = NamedSymbolTable()

valid = errorCheck(syn_tree,
                   sym_table,
                   named_sym_table,
                   parser.lexer.infileLines)

ctx = ir.global_context
llvm_custom_types = create_llvm_types(named_sym_table, ctx)
generated_ir = codegen(syn_tree, named_sym_table, {
    'mod': module,
    'llvm_custom_types': llvm_custom_types,
    'ctx': ctx,
})
print(module)
binding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()  # yes, even this one
binding.load_library_permanently('../runtime.so')

binding.parse_assembly(str(module), None)
engine = create_execution_engine()
mod = compile_ir(engine, str(module))

t_fun = CFUNCTYPE(c_int64, c_int64)
fact = t_fun(engine.get_function_address('global.fun1'))
print(fact(5, 7))
