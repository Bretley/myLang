#!/usr/bin/python
# Bret Barkley
# brb171@pitt.edu
from __main__ import *
import sys
import re

identifiers = "[a-z]([a-zA-Z]|[0-9])*"
types = "[A-Z][a-z]*"
numbers = "[0-9]+"
symbols = "->|=>|\{|\}|\[|\]|\(|\)|<=|>=|==|!=|=|<|>|;|\+|\-|\*|/|v|\^|,"
keywordsList = ["else","if","int","return","void","while","in","non","or","and", "not", "v"]
keywords = "|".join([x + "(?![a-zA-Z0-9])" for x in keywordsList])  # Use lookahead to make sure
commentStart = "/\*"
commentEnd = "\*/"

# matchPrint: handles logic of when to print based on matches
# Appends to the lex output if appropriate
def matchPrint(lexType, matched, lineCount, lexed):
    if matched != "" and ((matched != "/*" and matched != "*/") or lexType == "ERROR"):
        tmp = "(" + str(lineCount) + ",\"" + lexType + "\"," + "\"" + matched + "\")\n"
        lexed += tmp
    return lexed

# MatchCheck will handle regex logic, and most importantly, shrink infile by
# the length of the matched lexeme
def matchCheck(regex, string):
    matched = re.match(regex,string)
    if matched is not None:
        string = string[len(matched.group()):]
        return string, matched.group()
    else:
        return string, ""

# heavy-lifting method, handles most of the logic
def lex(infile):
    curSize = 0                 # Used to check if there was a match
    lineCount = 1               # Keep track of line nr.
    inComment = False           # Am I in a currently in an open comment?
    lastLine = 0                # Used to keep track of last Line comment was started on.
    lexed = ""                  # Final output. Is only ever appended to.
    while True:
        if len(infile) == 0:
            if inComment:
                lexed = matchPrint("ERROR", "/*", lastLine, lexed)
            return not inComment, lexed
                                                # Munch the whitespace if it's at the start
        while infile[0] in [" ","\t","\n"]:
            if infile[0] == "\n":
                lineCount += 1
            infile = infile[1:]
            if len(infile) == 0:                # Ending on whitespace is common, gotta make sure
                if inComment:
                    lexed = matchPrint("ERROR", "/*", lastLine, lexed)
                return not inComment, lexed

        if inComment:
            infile, matched = matchCheck(commentEnd, infile)
            if inComment and matched != "":
                inComment = False;                  # Valid comment closed
                continue

        if not inComment:                       # Not in comment => Check for lex tokens
            infile, matched = matchCheck(commentStart, infile)
            lexed = matchPrint("", matched, lineCount, lexed)
            if matched != "":
                lastLine = lineCount            # Mark first comment opening for error
                inComment = True                    # We are now in a comment
                continue
            curSize = len(infile)
            infile, matched = matchCheck(keywords, infile)
            lexed = matchPrint("KEY", matched, lineCount, lexed)
            if matched != "":
                continue
            infile, matched = matchCheck(identifiers, infile)
            lexed = matchPrint("ID", matched, lineCount, lexed)
            if matched != "":
                continue
            infile, matched = matchCheck(symbols, infile)
            lexed = matchPrint("SYM", matched, lineCount, lexed)
            if matched != "":
                continue
            infile, matched = matchCheck(types, infile)
            lexed = matchPrint("TYPE", matched, lineCount, lexed)
            if matched != '':
                continue
            infile, matched = matchCheck(numbers, infile)
            lexed = matchPrint("NUM", matched, lineCount, lexed)
            if len(infile) >= curSize:          # True if no match found, likely an invalid symbol. 
                lexed = matchPrint("ERROR", infile[0], lineCount, lexed)
                return False, lexed
        else:                                   # We are still in a comment, munch one char and check again
            infile = infile[1:]

# Main code starts here
class Lexer:
    def __init__(self, infile, outfile):
        infile = open(infile, "r+").read()
        outfile = open(outfile, "w+")
        self.infile = infile
        self.outfile = outfile
        self.successful, self.lexed = lex(infile)
        if self.successful: 
            self.outfile.write(self.lexed)

