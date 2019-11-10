from slr import SLRParser
import sys
parser = SLRParser("grammar.txt", sys.argv[1])

ast = parser.parse()[0]
print( ast)
cst = ast.simplify(parser.grammar)
cst = cst.simplify2()

# Am i anticipating a problem with carriage returns? who knows!
a = str(cst).replace(" ","").replace("\n","")
print( a)

