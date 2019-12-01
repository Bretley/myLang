from varClasses import *
from semantic import *
from errors import Error
"""
    Defines sum and product types and their behaviors
    Things we need to think about:
    - How are we going to handle union of sum and sum of union type signatures
    - ...
"""

defaultTypes = [
    "Int",
    "Float",
    "Bool",
    "Char",
]

def isDefault(t):
    return isDefault in defaultTypes

e = Error(sys.argv[1])
class SumInstance():
    pass

class ProductInstance():
    pass

class Sum():
    def __init__(self, ast, st):
        # typeBarList
        self.types = [x for x in ast[3] if x != '|']
        self.name = ast[1]
        self.signatures = {}
        self.members = {}
        for typeName in self.types:
            if typeName in defaultTypes:
                self.signatures[(typeName,)] = typeName
            else:
                # Product
                subType = st.findSymbol(typeName)
                if subType.signatures in self.signatures:
                    e.err(
                        "Sum type must be disjoint\n" + 
                        "Sum name: " + self.name + "\n"
                        "subTypes: " + self.signatures[subType.signatures] +
                        " and " + subType.name + '\n' + 
                        "both have signatures: " + str(subType.signatures)
                        , "semantic", ast.lineNum
                    )
                self.signatures[subType.signatures] = typeName

                # TODO: sum of sum

class Product():
    def __init__(self, ast, st):
        self.name = ast[1]
        self.members = []
        self.signatures = []
        for varDecl in ast[4]: # memberList
            for identifier in varDecl[1]:
                #TODO: check
                self.members.append(
                    Var(identifier, varDecl[0][0], len(varDecl[0][1]))
                )
                self.signatures.append(varDecl[0][0])
        self.members = tuple(self.members)
        self.signatures = tuple(self.signatures)
