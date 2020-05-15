#!/usr/bin/python
# Bret Barkley
# brb171@pitt.edu
from __main__ import *
import sys
import re

identifiers = "[a-z]([a-zA-Z]|[0-9])*"
types = "[A-Z][a-zA-Z0-9]*"
numbers = "[0-9]+"
floats = "[0-9]+\.[0-9]*"
string = "\".*\""
symbols = "\.|->|=>|\{|\}|\[|\]|\(|\)|<=|>=|==|!=|=|<|>|;|\+|\-|\*|/|v|\^|,|:|\|"
keywordsList = ["let","else","if","int","return","void","while","in","non","or","and", "not", "v",
        "type"]
keywords = "|".join([x + "(?![a-zA-Z0-9])" for x in keywordsList])  # Use lookahead to make sure
commentStart = "/\*"
commentEnd = "\*/"


def matchPrint(lexType, matched, lineCount, lexedString):
    lexTuple = ()
    if matched != "" and ((matched != "/*" and matched != "*/") or lexType == "ERROR"):
        tmp = "(" + str(lineCount) + ",\"" + lexType + "\"," + "\"" + matched + "\")\n"
        lexTuple = (lineCount, lexType, matched)
        lexedString += tmp
    return lexedString,  lexTuple


# MatchCheck will handle regex logic, and most importantly, shrink infile by
# the length of the matched lexeme
def matchCheck(regex, string):
    matched = re.match(regex,string)
    if matched is not None:
        string = string[len(matched.group()):]
        return string, matched.group()
    else:
        return string, ""

def get_matches(s):
    lex_items = {
        'identifiers': identifiers,
        'types': types,
        'numbers': numbers,
        'floats': floats,
        'string': string,
        'symbols': symbols,
        'keywords': keywords,
        'comment': comment
    }

    matches = []
    for lex_name in lex_items:
        m = re.match(lex_items[lex_name], s)
        if m:
            matches.append(m.group())
    return matches

# heavy-lifting method, handles most of the logic
def lex2(infile):
    curSize = 0
    lineCount = 1
    inComment = False
    lexed = ""
    lexedList = []
    target = '|'.join([lex_items[name] for name in lex_items])
    reg = re.compile(target)
    print(target)
    while True:
        if len(infile) == 0:
            break
        if infile[0] in ('\t', ' ', '\n'):
            infile = infile[1:]
            continue
        print(get_matches(infile))
        break




    print('lex')
    print(lexedList)
    sys.exit(1)

def lex(infile):
    curSize = 0                 # Used to check if there was a match
    lineCount = 1               # Keep track of line nr.
    inComment = False           # Am I in a currently in an open comment?
    lastLine = 0                # Used to keep track of last Line comment was started on.
    lexed = ""                  # Final output. Is only ever appended to.
    lexedList = []
    while True:
        if len(infile) == 0:
            if inComment:
                lexed, lexTuple = matchPrint("ERROR", "/*", lastLine, lexed)
                if lexTuple != ():
                    lexedList.append(lexTuple)
            return not inComment, lexed, lexedList
        # Munch the whitespace if it's at the start
        while infile[0] in [" ", "\t", "\n"]:
            if infile[0] == "\n":
                lineCount += 1
            infile = infile[1:]
            if len(infile) == 0:                # Ending on whitespace is common, gotta make sure
                if inComment:
                    lexed = matchPrint("ERROR", "/*", lastLine, lexed)
                return not inComment, lexed, lexedList

        if inComment:
            infile, matched = matchCheck(commentEnd, infile)
            if inComment and matched != "":
                inComment = False                  # Valid comment closed
                continue

        if not inComment:                       # Not in comment => Check for lex tokens
            infile, matched = matchCheck(commentStart, infile)
            lexed, lexTuple = matchPrint("", matched, lineCount, lexed)
            if lexTuple != ():
                lexedList.append(lexTuple)
            if matched != "":
                lastLine = lineCount            # Mark first comment opening for error
                inComment = True                    # We are now in a comment
                continue
            curSize = len(infile)
            infile, matched = matchCheck(keywords, infile)
            lexed, lexTuple = matchPrint("KEY", matched, lineCount, lexed)
            if lexTuple != ():
                lexedList.append(lexTuple)
            if matched != "":
                continue
            infile, matched = matchCheck(identifiers, infile)
            lexed, lexTuple = matchPrint("ID", matched, lineCount, lexed)
            if lexTuple != ():
                lexedList.append(lexTuple)
            if matched != "":
                continue
            infile, matched = matchCheck(symbols, infile)
            lexed, lexTuple = matchPrint("SYM", matched, lineCount, lexed)
            if lexTuple != ():
                lexedList.append(lexTuple)
            if matched != '':
                continue
            infile, matched = matchCheck(types, infile)
            lexed, lexTuple = matchPrint("TYPE", matched, lineCount, lexed)
            if lexTuple != ():
                lexedList.append(lexTuple)
            if matched != '':
                continue
            infile, matched = matchCheck(numbers, infile)
            lexed, lexTuple = matchPrint("NUM", matched, lineCount, lexed)
            if lexTuple != ():
                lexedList.append(lexTuple)
            if len(infile) >= curSize:          # True if no match found, likely an invalid symbol. 
                lexed = matchPrint("ERROR", infile[0], lineCount, lexed)
                return False, lexed, lexedList
        else:                                   # We are still in a comment, munch one char and check again
            infile = infile[1:]

# Main code starts here
class Lexer:
    def __init__(self, infile, outfile):
        infile = open(infile, "r+").read()
        self.infileLines = infile.split('\n')
        self.infile = infile
        self.successful, self.lexed, self.lexedList = lex(infile)

