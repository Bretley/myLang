from defaults import *

class ProductType:
    def __init__(self, members, typ):
        self.type = typ
        self.members = {n: (i, t) for i, (n, t) in enumerate(zip(members, typ))}
        print(self.type)
        print(self.members)


class NamedType:
    """ Class to represent a named or otherwise atomic type"""
    def __init__(self, name):
        if not isinstance(name, str):
            raise TypeError("name of NamedType is not string")
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return 'NamedType(' + self.name + ')'

    def __eq__(self, other):
        print(other)
        if other.name == '?':
            other.name = self.name
        elif self.name == '?':
            self.name = other.name
        elif other.name == 'non' and not isAtomic(self.name):
            return True
        elif self.name == 'non' and not isAtomic(other.name):
            return True
        return self.name == other.name

def tuple_str(typ):
    if isinstance(typ, tuple):
        return str(tuple(str(x) for x in typ))
    else:
        return str(typ)

class FunType:
    """ Class to represent single-arg curried function"""
    def __init__(self, args, to):
        self.args = args
        self.to = to

    def __str__(self):
        args, to = self.args, self.to
        args = tuple_str(args)

        to = tuple_str(to)
        if isinstance(to, FunType):
            to = '(' + str(to) + ')'
        return args + ' -> ' + to

    def args_eq(self, other):
        if isinstance(other, NamedType) and other.name == '?':
            other = self.args
            return True
        else:
            return self.args == other.args

class Type:
    """ Class to store type info of a var"""
    def __init__(self, typ, dimensions):
        self.type = typ
        self.dimensions = dimensions

    def __eq__(self, other):
        return self.type == other.type and self.dimensions == other.dimensions

    def __str__(self):
        return str(self.type) + '[]'*len(self.dimensions)


class Var:
    def __init__(self, name, typ, dimensions, info):
        self.name = name
        self.type = typ
        self.dimensions = dimensions
        self.info = info
        self.location = None

    def __str__(self):
        ret = str(self.type) + ' '
        if self.dimensions > 0:
            ret += '[]' * self.dimensions + ' '
        ret += self.name
        ret += ' (' + str(self.info) + ')'
        return ret


class Fun:
    def __init__(self, name, varType, paramNum):
        self.name = name
        self.type = varType
        self.paramNum = paramNum
        self.params = []


class Body:
    def __init__(self, funBodyASTNode):
        self.type = funBodyASTNode.type


class Function:
    def __init__(self, anonymousFunctionASTNode, st):
        self.params = Parameters(anonymousFunctionASTNode[0], st)
        self.body = Body(anonymousFunctionASTNode[2])
        self.returnType = self.body.type


class Parameters:
    def __init__(self, paramASTNode, st):
        self.params = []
        self.destructuredParams = []
        if paramASTNode[0] == 'non':
            return
        for param in paramASTNode[0]:
            print(param)
            if param != ',':
                pType = Type(param[0][0])
                if param[0].name == 'namedParam':
                    self.params.append((pType, param[0][1].children, False, []))
                elif param[0].name == 'destructuredParam':
                    self.params.append((pType, ['destructured' +
                                                param[0][0][0]], True, []))
                    typ = st.findSymbol(pType.baseType)
                    print('===')
                    print(param[0][2])
                    self.destructuredParams.append((typ.name, [
                        typ.get(x) for x in param[0][2]
                    ]))
        print(self.destructuredParams)
        print(self.params)

    def __str__(self):
        ret = '('
        varList = []
        for typeInfo, nameList, isDestructured, destructured in self.params:
            for childname in nameList:
                varList.append(str(typeInfo) + ' ' +
                               str(childname) +
                               '[]' * typeInfo.dimensions)
        ret += ', '.join(varList)
        ret += ')'
        return ret
