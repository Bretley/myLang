from dfa import DFA
from grammar import Grammar
from lex import Lexer
from AST import AST
from errors import Error
from separator import itemSeparator
import copy
import sys

class SLRParser:
    def __init__(self, fileName, cFile):
        self.e = Error(fileName)
        self.nodeStack = []
        self.fileName = fileName
        self.grammar = Grammar(open(fileName).read())
        self.dfa = DFA(self.grammar)
        self.stack = [("DummySymbol", self.dfa.startState)]
        self.lexer = Lexer(cFile, cFile + ".lex")
        """
        This bit's going to go away soon
        self.lexed = self.lexer.lexed
        self.lexed = [x for x in self.lexed.split("\n") if x != '']
        self.lexed = [eval(x) for x in self.lexed]
        """
        self.lexed = self.lexer.lexedList
        self.action = []
        self.terminals = self.grammar.terminals
        self.actions = {}
        # construct action table
        for state in self.dfa.transitionTable:
            self.actions[state] = {}
            for on in self.dfa.transitionTable[state]:
                self.actions[state][on] = ("error")
            self.actions[state]["$"] = ("error")
        for state in self.dfa.transitionTable:
            if "DummyStart -> " + self.grammar.startSymbol + " " + itemSeparator in state:
                if state not in self.actions:
                    self.actions[state] = {"$" : ("accept")}
                else:
                    self.actions[state]["$"] = ("accept")

            for transition in self.dfa.transitionTable[state]:
                actionState = self.dfa.goto(state, transition)
                if any([itemSeparator + " " + transition in x for x in state]) and actionState is not None:
                    if state not in self.actions:
                        self.actions[state] = {transition : ("shift", actionState)}
                    else:
                        self.actions[state][transition] = ("shift", actionState)
                if any([x[-1] == itemSeparator for x in state]):
                    matches = [x for x in state if x[-1] == itemSeparator]
                    matches = [x for x in matches if transition in self.grammar.getFollowSet(x.partition(" ")[0])]
                    for match in matches:
                        if match.partition(" ")[0] != "DummyStart":
                            reduceNum = len([x for x in match.partition(" -> ")[2].split(" ") if x != itemSeparator])
                            if state not in self.actions:
                                self.actions[state] = {transition : ("reduce", match.partition(" ")[0], transition, reduceNum)}
                            else:
                                self.actions[state][transition] = ("reduce", match.partition(" ")[0], transition, reduceNum)

    def parse(self):
        lexIndex = 0
        print( self.lexed)
        self.lexed.append((0,'KEY','$'))
        while True:
            lexItem = self.getLexItem(self.lexed[lexIndex])
            action = self.actions[self.stack[-1][1]][lexItem]
            if action[0] == "shift":
                self.stack.append((self.getLexItem((self.lexed[lexIndex])), action[1], self.lexed[lexIndex]))
                self.nodeStack.append(lexItem)
                lexIndex += 1
            elif action[0] =="reduce":
                children = []
                for pop in range(action[3]):
                    lexVal = self.nodeStack.pop()
                    if lexVal == "ID" or lexVal == "NUM" or lexVal == "TYPE":
                        lexVal = self.stack[-1][2][2]
                    children.append(lexVal)
                    self.stack.pop()
                children = list(reversed(children))
                self.stack.append((action[1], self.dfa.goto(self.stack[-1][1], action[1]), self.lexed[lexIndex]))
                astChildren = [x for x in children if isinstance(x, AST)]
                if astChildren != []:
                    self.nodeStack.append(AST(action[1], children, min([x.lineNum for x in astChildren])))
                else:
                    self.nodeStack.append(AST(action[1], children, self.lexed[(lexIndex)][0]))

            elif action == ("error"):
                # Debugging like a pro
                print( self.lexed[lexIndex])
                print( )
                print( "Syntax Error:")
                errorLine = self.lexed[lexIndex][0]-1
                print( "Found on line: " + str(errorLine))
                for offset in range(-3, 3):
                    if (errorLine+offset) >= 0 and (errorLine+offset) < len(self.lexer.infileLines):
                        pref = '  ' if (offset != 0) else '>>'
                        print( pref + self.lexer.infileLines[errorLine + offset])
                print( "==========")
                print( lexIndex)
                print( "lexItem = " + str(lexItem) + " ->  " + str(self.lexed[lexIndex]))
                print( "action = " + str(action))
                print( "STACK")
                print(("...."))
                for x in self.stack[-4:-1]:
                    print( x[0])
                print( self.stack[-1][1])
                a = self.dfa.transitionTable[self.stack[-1][1]]
                b = {}
                for key in a:
                    if a[key] != () and self.grammar.isTerminal(key):
                        b[key] = a[key]
                print( b)
                return None
            elif action == ("accept"):
                break
        return self.nodeStack


    def getLexItem(self, lexItem):
        if lexItem[1] in ["KEY","SYM"]:
            return lexItem[2]
        else:
            return lexItem[1]


