""" Defines things used for error reporting """
import sys


class Error:
    def __init__(self, f_name):
        with open(f_name, 'r') as f:
            self.file = f.read().split('\n')

    def message(self, msg_type, msg, e_type, line):
        print(msg_type)
        print(e_type + ' error on  line:' + str(line))
        line -= 1
        for offset in range(-3 + line, 3 + line):
            if 0 <= offset < len(self.file):
                pref = '  ' if (offset != line) else '>>'
                print(pref + self.file[offset])
        print(msg)

    def warn(self, cond, msg, e_type, line):
        if cond:
            self.message('Warning: ', msg, e_type, line)

    def err_if(self, cond,  msg, e_type, line):
        if cond:
            self.message('Error: ', msg, e_type, line)
            sys.exit(0)
