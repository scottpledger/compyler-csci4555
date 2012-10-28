from ir import *

class Push(Node):
    def __init__(self, arg):
        self.arg = arg

    def getChildren(self):
        return [arg]

    def getChildNodes(self):
        return [arg]

    def __repr__(self):
        return "Push(%s)" % repr(self.arg)

class Pop(Node):
    def __init__(self, bytes):
        self.bytes = bytes

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "Pop(%s)" % repr(self.bytes)

class PopValue(Node):
    def __init__(self, target):
        self.target = target

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "PopValue(%s)" % repr(self.target)

class CallX86(Node):
    def __init__(self, name):
        self.name = name

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "call %s" % self.name


class CMPLInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)

# lhs must be a single byte register (such as the AL part of EAX).
class SetIfEqInstr(ArithInstr):
    def __init__(self, lhs, rhs=[]):
        ArithInstr.__init__(self, lhs, rhs)

class SetIfNotEqInstr(ArithInstr):
    def __init__(self, lhs, rhs=[]):
        ArithInstr.__init__(self, lhs, rhs)

class IntMoveZeroExtendInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)

class JumpEqInstr(Node):
    def __init__(self, dest):
        self.dest = dest

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "je(%s)" % self.dest

class IntNotInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)


class IndirectCallX86(Node):
    def __init__(self, funptr):
        self.funptr = funptr

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "call (%s)" % self.funptr
