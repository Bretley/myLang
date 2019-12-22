""" Defines things used for error reporting """
import sys

class Error:
    def __init__(self, fileName):
        with open(fileName, 'r') as f:
            self.file = f.read().split('\n')

    def warn(self, msg, errType, lineNum):
        print( 'Warning:')
        print( errType + ' error on  line:' + str(lineNum))
        lineNum -= 1
        for offset in range(-3, 3):
            if (lineNum+offset) >= 0 and (lineNum+offset) < len(self.file):
                pref = '  ' if (offset != 0) else '>>'
                print( pref + self.file[lineNum + offset])
        print( msg)
    def err(self, msg, errType, lineNum): 
        print( errType + ' error on  line:' + str(lineNum))
        lineNum -= 1
        for offset in range(-3, 3):
            if (lineNum+offset) >= 0 and (lineNum+offset) < len(self.file):
                pref = '  ' if (offset != 0) else '>>'
                print( pref + self.file[lineNum + offset])
        print( msg)
        sys.exit(0)
