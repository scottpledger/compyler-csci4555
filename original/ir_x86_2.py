from ir_x86 import *
from ir2 import *

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
