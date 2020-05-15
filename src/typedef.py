import sys
from defaults import *
from varClasses import Var
from errors import Error
"""
    Defines sum and product types and their behaviors
    Things we need to think about:
    - How are we going to handle union of sum and sum of union type signatures
    - ... nested tree thing?
"""


""" Represents type information of a variable """


class SumInstance():
    pass

class ProductInstance():
    pass

e = Error(sys.argv[1])
""" represents the definition of a sum type """
class Sum():
    def __init__(self, ast, st):
        # typeBarList
        self.types = [x for x in ast[3] if x != '|']
        self.name = ast[1]
        self.signatures = {}
        self.members = {}
        for typeName in self.types:
            if isDefault(typeName):
                if (typeName,) in self.signatures:
                    e.warn(
                        'Sum type has duplicate type in definition\n'
                        'Sum name: ' + self.name + '\n'
                        'Duplicate type: ' + typeName + '\n',
                        'Semantic', ast.lineNum
                    )
                self.signatures[(typeName,)] = typeName
            elif st.findSymbol(typeName) is None:
                e.err(
                    'Sum type references type that has not been defined\n' + 
                    'Sum name: ' + self.name + '\nUndefined type: ' + typeName,
                    'Semantic', ast.lineNum
                )
            else:
                # Product
                subType = st.findSymbol(typeName)
                if isinstance(subType, Product):
                    #TODO: this is going to have to change
                    if subType.signatures in self.signatures:
                        e.err(
                            'Sum type must be disjoint\n' + 
                            'Sum name: ' + self.name + '\n'
                            'subTypes: ' + self.signatures[subType.signatures] +
                            ' and ' + subType.name + '\n' + 
                            'both have signatures: ' + str(subType.signatures)
                            , 'semantic', ast.lineNum
                        )
                    self.signatures[subType.signatures] = typeName
                elif isinstance(subType, Sum):
                    """ Probably some kind of recursive thing ?"""
                    # Get a thing (first one) if there is an x in signatures
                    test = next((x for x in subType.signatures.keys() if x in self.signatures), None)
                    if test is not None:
                        e.err(
                                'Sum types must be disjoint\n' + 
                                'Sum name: ' + self.name + '\n' + 
                                'conflicting Subtypes: ' + subType.name + ' and ' + self.signatures[test] + '\n' +
                                'both have constructors of type signature: ' + str(test),
                                "Semantic", ast.lineNum
                        )
                    for x in subType.signatures:
                        self.signatures[x] = subType.name
        print( self.name)
        print( self.signatures)  

""" represents the defintiion of a product type """
class Product():
    def __init__(self, ast, st):
        self.name = ast[1]
        self.members = []
        self.signatures = []
        for var in ast[4]:  # memberList
            for identifier in var[1]:
                # TODO: check
                self.members.append(
                    Var(identifier, var[0][0], len(var[0][1]), 'Product')
                )
                self.signatures.append(var[0][0])
        self.members = tuple(self.members)
        self.signatures = tuple(self.signatures)

    def get(self, name):
        for var in self.members:
            if name == var.name:
                return var
        else:
            return None


