from ir1 import *

class IntCompareInstr(Node):
    def __init__(self, name, lhs, rhs):
        self.name = name
        self.lhs = lhs
        self.rhs = rhs

    def getChildren(self):
        return [self.lhs] + self.rhs

    def getChildNodes(self):
        return [self.lhs] + self.rhs

    def __repr__(self):
        return "%s <- %s(%s)" % (repr(self.lhs), self.name, \
                                 ','.join([repr(c) for c in self.rhs]))


class IntAndInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)


class IntOrInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)


class BoolToIntInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)


class IntToBoolInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)


class ShiftLeftInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)


class ShiftRightInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)


class CondGoto(Node):
    def __init__(self, cond, then_l, else_l):
        self.cond = cond
        self.then_l = then_l
        self.else_l = else_l

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "CondGoto(%s, %s, %s)" % \
               (self.cond, self.then_l, self.else_l)

class Goto(Node):
    def __init__(self, target_l):
        self.target_l = target_l

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "Goto(%s)" % self.target_l

class Phi(Node):
    def __init__(self, result, var1, label1, var2, label2):
        self.result = result
        self.var1 = var1
        self.label1 = label1
        self.var2 = var2
        self.label2 = label2
        
    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "%s = phi(%s <- %s, %s <- %s)" % \
               (self.result, self.var1, self.label1, self.var2, self.label2)

class Label(Node):
    def __init__(self, name):
        self.name = name

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "Label(%s)" % self.name

