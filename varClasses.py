class Var:
    def __init__(self, name, baseType, dimensions):
        self.name = name
        self.type = baseType
        self.dimensions = dimensions

    def __str__(self):
        ret = self.type + ' '
        if self.dimensions > 0:
            ret += '[]'*self.dimensions + ' '
        ret += self.name
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
    def __init__(self, anonymousFunctionASTNode):
        self.params = Parameters(anonymousFunctionASTNode[0])
        self.body =  Body(anonymousFunctionASTNode[2])
        self.returnType = self.body.type

class Type: 
    def __init__(self, typeSpecifierASTNode):
        self.baseType = typeSpecifierASTNode[0]
        self.dimensions = len(typeSpecifierASTNode[1].children)

    def __eq__(self, other):
        return (self.dimensions == other.dimensions and
                self.baseType == other.baseType)

    def __str__(self):
        return self.baseType.lower()


class Parameters:
    def __init__(self, paramASTNode):
        self.params = []
        if paramASTNode[0] == 'non':
            return
        for param in paramASTNode[0]:
            if param != ',':
                self.params.append((Type(param[0]), param[1].children))

    def __str__(self):
        ret = '('
        varList = []
        for typeInfo, nameList in self.params:
            for childname in nameList:
                varList.append(str(typeInfo) + ' ' + 
                        str(childname) +
                        '[]'*typeInfo.dimensions)
        ret += ', '.join(varList)
        ret += ')'
        return ret

