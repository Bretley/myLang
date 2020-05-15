from grammar import Grammar
from separator import *
class DFA:
    def __init__(self, grammar):
        self.transitionTable = {}
        lhsArr = grammar.getLHS()
        items = grammar.getItems()
        self.itemMap = {}
        self.grammar = grammar
        self.startState = "DummyStart -> " + itemSeparator + " " + grammar.getStartSymbol()
        self.state = self.startState
        # Prelim transition table setup
        for lhs in lhsArr:
            for itemSet in items[lhs]:
                # index = index of .
                for index, item in enumerate(itemSet):
                    name = self.itemString(lhs, item)
                    self.transitionTable[name] = {"epsilon": []}
                    if lhs not in self.itemMap:
                        self.itemMap[lhs] = []
                    self.itemMap[lhs].append(name)
                    if index < len(item) - 1:
                        self.transitionTable[name][item[index + 1]] = [self.itemString(lhs, itemSet[index+1])]

        for lhs in lhsArr:
            for itemSet in items[lhs]:
                # index = index of .
                for index, item in enumerate(itemSet):
                    name = self.itemString(lhs, item)
                    if index < len(item) - 1 and not grammar.isTerminal(item[index+1]):
                        for epsilonTransition in self.itemMap[item[index+1]]:
                            if "-> " + itemSeparator in epsilonTransition: # only puy .X in
                                self.transitionTable[name]["epsilon"].append(epsilonTransition)


        # Currently still in NFA mode, have to convert
        # Subset construction
        self.transitions = set([])
        for state in self.transitionTable:
            itemChunk = state.partition(" -> ")[2].split(" ")
            for transition in itemChunk:
                if transition != itemSeparator and transition != "":
                    self.transitions.add(transition)


        self.transitions.add("$")
        Dstates = {}
        unMarked = []
        StartState = self.epsilonClosure([self.startState])
        Dstates[tuple(StartState)]  = {}
        unMarked = [StartState]
        while len(unMarked) != 0:
            current = unMarked.pop()
            for on in self.transitions:
                movedState = self.epsilonClosure(self.move(current, on))
                if tuple(movedState) not in Dstates:
                    Dstates[tuple(movedState)] = {}
                    unMarked.append(movedState)
                Dstates[tuple(current)][on] = tuple(movedState)

        #print( len(self.transitionTable))
        #print( len(Dstates))
        for state in Dstates:
            for on in Dstates[state]:
                if Dstates[state][on] not in Dstates:
                    print( Dstates[state][on])
        self.transitionTable = Dstates
        self.startState = tuple(StartState)


    def setState(self, state):
        self.state = state

    def transition(self, inputSymbol):
        if inputSymbol in self.transitionTable[self.state]:
            self.state = self.transitionTable[self.state][inputSymbol]
        else:
            print("ERROr No DFA Transition?")

    def goto(self, state, inputSymbol):
        if inputSymbol in self.transitionTable[state]:
            return self.transitionTable[state][inputSymbol]
        else:
            #print("ERROr No DFA Transition?")
            return None

    def epsilonClosure(self, stateSet):
        stack = []
        for nfaState in stateSet:
            stack.append(nfaState)
        ret = set(stateSet)
        while len(stack) > 0:
            currentState = stack.pop()
            for epsilonTransition in self.transitionTable[currentState]["epsilon"]:
                if epsilonTransition not in ret:
                    ret.add(epsilonTransition)
                    stack.append(epsilonTransition)
        return ret

    def move(self, stateSet, on):
        ret = set()
        for state in stateSet:
            if on in self.transitionTable[state]:
                for transition in self.transitionTable[state][on]:
                    ret.add(transition)
        return ret

    def itemString(self, lhs, item):
        return lhs + " -> " + " ".join(item)

