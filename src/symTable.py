""" Basic Symbol Table implemented with stack 
    Non permanent
"""
class SymbolTable:
    def __init__(self):
        self.stack = []
    def enterScope(self):
        self.stack.append({})
    def exitScope(self):
        return self.stack.pop()
    def findSymbol(self,symbol):
        for nested in reversed(self.stack):
            if symbol in nested:
                return nested[symbol]
        return None
    def addSymbol(self,symbol):
        self.stack[-1][symbol.name] = symbol
    def checkScope(self,symbolName):
        return symbolName in self.stack[-1]

""" Tree based map of symbol table info
Designed to be a reusable symbol table rather than an impermanent one
"""

class NamedSymbolTable():
    def __init__(self):
        self.root = 'global'
        self.tree = {self.root:{}}
        self.path = [self.root]
        self.currentScope = self.tree[self.root]

    def enterScope(self, name):
        if name not in self.currentScope:
            print( 'name not in current scope')
        self.currentScope = self.currentScope[name]
        self.path.append(name)

    def exitScope(self):
        self.path.pop(-1)
        self.currentScope = self.tree
        for name in self.path:
            self.currentScope = self.currentScope[name]

    def setScope(self, scope):
        tmp = self.tree
        for name in self.path[:-1]:
            tmp = tmp[name]
        tmp[self.path[-1]] = scope

    def addScope(self, name, scope):
        self.currentScope[name] = scope

    def __str__(self):
        return self.str(0, self.tree)

    def str(self, depth, curScope):
        ret = ''
        for key in curScope:
            ret += '   '*(depth) + key + ': '
            if isinstance(curScope[key], dict):
                ret +=  '\n' + self.str(depth+1, curScope[key])
            else:
                ret += str(curScope[key]) + '\n'
        return ret








