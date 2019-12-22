from defaults import *
class Type: 
    def __init__(self, typeSpecifierASTNode):
        self.baseType = typeSpecifierASTNode[0]
        self.dimensions = len(typeSpecifierASTNode[1].children)

    def __eq__(self, other):
        return (self.dimensions == other.dimensions and
                self.baseType == other.baseType)

    def __str__(self):
        if isDefault(self.baseType):
            return self.baseType.lower()
        else:
            return self.baseType + '*'


class Var:
    def __init__(self, name, typ, dimensions, info):
        self.name = name
        self.type = typ
        self.dimensions = dimensions
        self.info = info

    def __str__(self):
        ret = self.type + ' '
        if self.dimensions > 0:
            ret += '[]'*self.dimensions + ' '
        ret += self.name
        ret += ' (' + self.info+ ')'
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
    def __init__(self, anonymousFunctionASTNode,st):
        self.params = Parameters(anonymousFunctionASTNode[0],st)
        self.body =  Body(anonymousFunctionASTNode[2])
        self.returnType = self.body.type

class Parameters:
    def __init__(self, paramASTNode,st):
        self.params = []
        self.destructuredParams = []
        if paramASTNode[0] == 'non':
            return
        for param in paramASTNode[0]:
            print( param)
            if param != ',':
                pType = Type(param[0][0])
                if param[0].name == 'namedParam':
                    self.params.append((pType, param[0][1].children, False,[]))
                elif param[0].name == 'destructuredParam':
                    self.params.append((pType, ['destructured' +
                        param[0][0][0]], True,[]))
                    typ = st.findSymbol(pType.baseType)
                    print( '===')
                    print( param[0][2])
                    self.destructuredParams.append((typ.name,[
                        typ.get(x) for x in param[0][2]
                        ]))
        print( self.destructuredParams)
        print( self.params)

    def __str__(self):
        ret = '('
        varList = []
        for typeInfo, nameList, isDestructured, destructured in self.params:
            for childname in nameList:
                varList.append(str(typeInfo) + ' ' + 
                        str(childname) +
                        '[]'*typeInfo.dimensions)
        ret += ', '.join(varList)
        ret += ')'
        return ret

