from grammar import Grammar


g = Grammar(open("grammar.txt").read())
startString = "DummyStart"
recurDepth = 12

def recurGen(curDepth,maxDepth, stringSoFar):
    valid = True
    for sym in stringSoFar.split(" "):
        if not g.isTerminal(sym):
            valid = False
            break
    if valid:
        print( stringSoFar)
        return
    elif curDepth == maxDepth:
        return
    else:
        strlist = stringSoFar.split(" ")
        for index,replaceMe in enumerate(strlist):
            if g.isTerminal(replaceMe):
                continue
            else:
                for productions in g.getProd(replaceMe):
                    newList = [x for x in strlist]
                    newList[index] = " ".join(productions)
                    recurGen(curDepth + 1, maxDepth, " ".join(newList))





recurGen(0, recurDepth, startString)
print( g.isTerminal("var-declaration"))
