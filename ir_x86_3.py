from ir_x86_2 import *

class IndirectCallX86(Node):
    def __init__(self, funptr):
        self.funptr = funptr

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "call (%s)" % self.funptr
