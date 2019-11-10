import json
class Grammar:
    def __init__(self, specString): 
        self.spec = specString
        self.lhs = ["DummyStart"]
        self.grammarTable = {}
        self.firstSets = {}
        self.firstStack = []
        self.followSets = {}
        self.items = {}
        self.leftovers = []
        self.nullable = {}
        self.nullableStack = []
        self.terminals = set([])
        # Initalize Table of productions
        grammarLines = [x for x in specString.split("\n") if x != ""]
        self.startSymbol = grammarLines[0].split(" --> ")[0]
        self.followSets[self.startSymbol] = set(["$"])
        self.startSymbol = grammarLines[0].split(" --> ")[0]
        self.orderedGrammarTable = []
        for index,line in enumerate(grammarLines):
            lhs, rhs = line.split(" --> ")
            self.lhs.append(lhs)
            rhs = rhs.split(" | ")
            rhs = [x.split(" ") for x in rhs]
            for x in rhs:
                for y in x:
                    if y == "empty":
                        self.nullable[lhs] = True

            self.items[lhs] = []
            self.grammarTable[lhs] = rhs
            self.orderedGrammarTable.append({lhs:rhs})
            if lhs not in self.followSets:
                self.followSets[lhs] = set([])
        open('grammar.JSON','w+').write(json.dumps(self.orderedGrammarTable,indent=True))
        self.firstSets["DummyStart"] = set()
        self.followSets["DummyStart"] = set()
        self.grammarTable["DummyStart"] = [[self.startSymbol]]
        self.items["DummyStart"] = []
        self.enhanceNullable()
        self.genFirstAndFollowSets()
        self.genItems()
        self.genTerminals()
    def genTerminals(self):
        for lhs in self.grammarTable:
            for production in self.grammarTable[lhs]:
                for produced in production:
                    if produced != '' and produced != 'empty' and self.isTerminal(produced):
                        self.terminals.add(produced)


    def getItems(self):
        return self.items
    
    def getFollowSet(self, symbol):
        return self.followSets[symbol]

    def getFirstSet(self, symbol):
        if self.isTerminal(symbol):
            return set([symbol])
        else:
            return self.firstSets[symbol]

    def hasTerminal(self, prodList):
        return any([self.isTerminal(x) for x in prodList])

    def enhanceNullable(self):
        for lhs in self.grammarTable:
            if lhs not in self.nullable:
                self.recursiveNullable(lhs)

    def recursiveNullable(self, symbol):
        self.nullableStack.append(symbol)
        nullable = False
        for production in self.grammarTable[symbol]:
            if self.hasTerminal(production):
                continue
            for index,producedItem in enumerate(production):
                if producedItem in self.nullable:
                    if self.nullable[producedItem] == True:
                        if index == len(production) - 1:
                            self.nullable[symbol] = True
                            self.nullableStack.pop()
                            return True
                        continue
                    else:
                        break
                else:
                    # Produced item is not yet determined
                    if symbol in self.nullableStack:
                        self.nullable[symbol] = False
                        return False
                    if self.recursiveNullable(producedItem):
                        if index == len(production) - 1:
                            self.nullable[symbol] = True
                            self.nullableStack.pop()
                            return True
                        continue
                    else:
                        break

        self.nullableStack.pop()
        self.nullable[symbol] = False
        return False
        
    def isNullable(self, symbol):
        if symbol not in self.nullable:
            return False
        return self.nullable[symbol]

    def genFirstAndFollowSets(self):
        # TODO: Gen first and follow sets
        # First sets
        for lhs in self.grammarTable:
            first = self.genFirstSet(lhs,lhs)
            #print( "FIRST(" + lhs + ")", first)
            self.firstSets[lhs] = first
        # Follow Sets
        for i in range(5):
            for lhs in self.grammarTable:
                self.genFollowSets(lhs)
        #print( self.followSets)

    def genFirstSet(self, curSymbol, startSymbol):
        if self.isTerminal(curSymbol):
            return set([curSymbol])
        else:
            self.firstStack.append(curSymbol)
            ret = set([])
            for production in self.grammarTable[curSymbol]:
                willAddEmpty = True
                for producedItem in production:
                    if self.isTerminal(producedItem):
                        # Item is a terminal
                        ret.add(producedItem)
                        willAddEmpty &= (producedItem == "empty")
                        break
                    else:
                        # Item is a nonterminal
                        if producedItem in self.firstStack:
                            if self.isNullable(producedItem):
                                continue
                            else:
                                willAddEmpty = False
                                break
                        else:
                            childSet = self.genFirstSet(producedItem, startSymbol)
                            willAddEmpty &= ("empty" in childSet)
                            if "empty" in childSet:
                                childSet.remove("empty")
                            ret = ret.union(childSet)
                    if not willAddEmpty:
                        break

                if willAddEmpty:
                    ret.add("empty")
            self.firstStack.pop()
            return ret

    # TODO: Fix me dammit
    def genFollowSets(self, curSymbol):
        ret = set([])
        for lhs in self.grammarTable:
            for production in self.grammarTable[lhs]:
                currentNullable = False
                if len(production) == 1 and not self.isTerminal(production[0]):
                    self.followSets[production[0]] = self.followSets[production[0]].union(self.followSets[lhs])
                for index, produced in reversed(list(enumerate(production))):
                    prev = None
                    if index < len(production) - 1:
                        prev = production[index + 1]
                    if prev is not None:
                        # Prev is defined, index + 1 >= len(prod) - 1,
                        # .., produced, prev, ...
                        if not self.isTerminal(produced):
                            if not self.isTerminal(prev):
                                # X -> A B
                                #print( produced, prev)
                                update = self.getFirstSet(prev).copy()
                                update.discard("empty")
                                update = self.followSets[produced].union(update)
                                #print( update)
                                self.followSets[produced] = update.copy()
                                if self.isNullable(prev):
                                    #TODO add conditional to 'drag' values
                                    currentNullable = True
                                    self.followSets[produced] = self.followSets[produced].union(self.followSets[lhs])
                                else:
                                    currentNullable = False

                            else:
                                pass
                                # X -> A b
                                self.followSets[produced].add(prev)
                                currentNullable = False
                    elif index == len(production) - 1 and not self.isTerminal(produced):
                                update = self.followSets[lhs].copy()
                                update.discard("empty")
                                update = self.followSets[produced].union(update)
                                self.followSets[produced] = update
        return ret
    
    def genItems(self):
        for lhs in self.grammarTable:
            for production in self.grammarTable[lhs]:
                cur = []
                for x in range(len(production)+1):
                    if x < len(production) and production[x] == "empty":
                        cur.append(["."])
                        break
                    cur.append(production[0:x] +  ["."] + production[x:len(production)])
                self.items[lhs].append(cur)


    def getStartSymbol(self):
        return self.startSymbol

    def getLHS(self):
        return self.lhs

    def getProd(self, lhs):
        return self.grammarTable[lhs]

    def isTerminal(self, curSymbol):
        return curSymbol not in self.grammarTable



    


