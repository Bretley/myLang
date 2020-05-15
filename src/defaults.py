defaultTypes = (
    "Int",
    "Float",
    "Bool",
    "Char",
    "String",
)

atomicTypes = (
    'Int',
    'Float',
    'Bool',
    'Char'
)


def isDefault(t):
    return t in defaultTypes

def isAtomic(t):
    return t in atomicTypes
