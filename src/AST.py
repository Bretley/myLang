import copy


def asts(ast):
    """Returns a list containing only ASTs from a given collection
    AST class supports iteration, so the input can be a list or not

    Args:
        ast: AST or List

    Returns:
        List of ASTs

    """
    return [x for x in ast if isinstance(x, AST)]


def flattenLists(ast):
    """Method to convert AST linked-style lists to a flat list
    Args:
        ast: AST to be converted/flattened

    Returns:
        the full AST with flattened lists
    """
    if not isinstance(ast, AST):
        return [ast]
    children = []
    for child in ast.children:
        children += flattenLists(child)
    if ast.isList() and ast.parent.isList() and ast.name == ast.parent.name:
        return children
    else:
        return [AST(ast.name, children, ast.lineNum)]


class AST:
    def __init__(self, name, children, lineNum):
        self.lhs = None
        self.name = name
        self.children = children
        self.type = None
        self.caseNum = None
        self.selectionResolution = None
        self.cstr = None
        self.cCode = None
        self.hoists = []
        self.lineNum = lineNum
        self.parent = None
        self.namedProd = None
        self.names = ()
        for child in asts(self.children):
            child.setParent(self)

    def isList(self):
        """Boolean of whether the name indicates a list"""
        return 'list' in self.name or 'List' in self.name

    def case(self, number):
        """Returns boolean of caseNum, used for if statements"""
        return self.caseNum == number

    def __iter__(self):
        self.counter = 0
        return self

    def __next__(self):
        return self.next()

    def next(self):
        if self.counter < len(self.children):
            ret = self.children[self.counter]
            self.counter += 1
            return ret
        else:
            raise StopIteration

    def __getitem__(self, index):
        return self.children[index]

    def str(self, depth):
        pad = ' '*depth
        ret = pad + "[" + self.name + ": " + str(self.type)
        ret += ' : ' + str(self.lineNum)
        for child in self.children:
            ret += "\n"
            if isinstance(child, AST):
                ret += child.str(depth+1)
            else:
                ret += pad + ' ' + " [" + str(child) + "]"
        ret += '\n' + pad + "]"
        return ret

    def genCases(self, grammar):
        self.caseNum = 0
        productions = []
        if self.name not in ('ID', 'CONSTANT', 'TYPE', 'NUM'):
            productions = grammar.getProd(self.name)
            self.namedProd = [x.name if isinstance(x, AST) else x for x in self.children]
            if not self.namedProd:
                self.namedProd = ['empty']
            self.caseNum = productions.index(self.namedProd)

        for child in self:
            if isinstance(child, AST):
                child.genCases(grammar)

    def __str__(self):
        return self.str(0)

    def __len__(self):
        return len(self.children)

    def setParent(self, parent):
        self.parent = parent
