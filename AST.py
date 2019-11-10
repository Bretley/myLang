import copy
import sys

def flattenLists(ast, parentIsList, parentName):
    if not isinstance(ast, AST):
        return [ast]
    if ast.isList() and parentIsList and parentName == ast.name:
        ret = []
        for child in ast.children:
            ret += flattenLists(child, True, ast.name)
        return ret
    else:
        ret = []
        for child in ast.children:
            ret += flattenLists(child, ast.isList() , ast.name)
        return [AST(ast.name, ret)]

class AST:
    def __init__(self, name, children):
        self.name = name
        self.children = children
        self.type = None
        self.caseNum = None
        self.selectionResolution = None

    """ boolean of whether or not this node is a list.
    This is mostly a helper for flattening lists"""
    def isList(self):
        return ('list' in self.name or 'List' in self.name)

    """ boolean of which production was chosen """
    def case(self, number): 
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
        ret = pad + "[" + self.name
        for child in self.children:
            ret += "\n"
            if isinstance(child, AST):
                ret += child.str(depth+1)
            else:
                ret += pad + ' ' + " [" + str(child) +"]"
        ret += '\n' + pad + "]"
        return ret

    def genCases(self, grammar):
        productions = grammar.getProd(self.name)
        viableProds = copy.deepcopy(productions)
        # Prune by length first
        viableProds = [x for x in viableProds if len(x) == len(self.children)]
        if len(viableProds) == 1:
            self.caseNum = productions.index(viableProds[0])
        elif 'list' in self.name or 'List' in self.name:
            self.caseNum = 0
        else:
            # loop over all remaining productions of equal length
            for prodIndex, prod in enumerate(viableProds):
                found = True
                for itemIndex, (item, child) in enumerate(zip(prod,self.children)):
                        if grammar.isTerminal(item):
                            found = found and not isinstance(child, AST)
                            if item == 'NUM':
                                found = found and (child.isdigit())
                            elif item == 'ID':
                                found = found and not child[0].isdigit()
                            else:
                                found = found and (item == child)
                        else:
                            found = found and isinstance(child, AST) and (item == child.name)
                if found:
                    self.caseNum = prodIndex
                    break

        for child in self:
                if isinstance(child, AST):
                    child.genCases(grammar)

    def __str__(self):
        return self.str(0)

    def __len__(self):
        return len(self.children)
