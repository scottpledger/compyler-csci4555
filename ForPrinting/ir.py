import compiler
from compiler.ast import *

class ArithInstr(Node):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def getChildren(self):
        return [self.lhs] + self.rhs

    def getChildNodes(self):
        return [self.lhs] + self.rhs

    def __repr__(self):
        return "%s(%s, [%s])" % (self.__class__.__name__, \
                                 repr(self.lhs), \
                                 ','.join([repr(c) for c in self.rhs]))
    

class IntAddInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)

class IntSubInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)

class IntLEAInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)

class IntMoveInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)


class IntNegInstr(ArithInstr):
    def __init__(self, lhs, rhs):
        ArithInstr.__init__(self, lhs, rhs)

class Call(Node):
    def __init__(self, name, lhs, rhs):
        self.name = name
        self.lhs = lhs
        self.rhs = rhs

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "%s <- call %s(%s)" % (repr(self.lhs), self.name, \
                                 ','.join([repr(c) for c in self.rhs]))

class Register(Node):
    def __init__(self, name):
        self.name = name

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "Register(%s)" % self.name

def assigned_vars(n):
    if isinstance(n, Stmt):
        return reduce(lambda a,b: a | b, \
                      [assigned_vars(s) for s in n.nodes], set([]))
    elif isinstance(n, ArithInstr):
        if isinstance(n.lhs, Name):
            return set([n.lhs.name])
        else:
            return set([])
    elif isinstance(n, Call):
        if n.lhs:
            return set([n.lhs.name])
        else:
            return set([])
    else:
        return set([])

# the following don't get used until closure conversion
# so they don't really belong here. -Jeremy


class FunName(Node):
    def __init__(self, name, lineno=None):
        self.name = name
        self.lineno = lineno

    def getChildren(self):
        return self.name,

    def getChildNodes(self):
        return ()

    def __repr__(self):
        return "FunName(%s)" % (repr(self.name),)

class IndirectCallFunc(Node):
    def __init__(self, node, args):
        self.node = node
        self.args = args

    def getChildren(self):
        children = []
        children.append(self.node)
        children.extend(flatten(self.args))
        return tuple(children)

    def getChildNodes(self):
        nodelist = []
        nodelist.append(self.node)
        nodelist.extend(flatten_nodes(self.args))
        return tuple(nodelist)

    def __repr__(self):
        return "IndirectCallFunc(%s, %s)" % (repr(self.node), repr(self.args))

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

