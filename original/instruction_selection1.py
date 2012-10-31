###############################################################################
# Instruction Selection
# This is a very naive version (easy to implement)

# Some of the code is more general than it needs to be for P_0.

# Input: an AST for P_1
# Output: an AST for IR_x86

from ir_x86 import *
from vis import Visitor

def make_arith(klass, lhs, rhs):
    if isinstance(lhs, Name) and isinstance(rhs, Name):
        return [IntMoveInstr(Register('eax'), [rhs]),
                klass(lhs, [Register('eax')])]
    else:
        return [klass(lhs, [rhs])]

def name_or_reg(n):
    return isinstance(n, Name) or isinstance(n, Register)

class InstrSelVisitor(Visitor):

    def __init__(self):
        Visitor.__init__(self)
    
    def visitModule(self, n):
        ss = self.dispatch(n.node)
        return Module(n.doc, ss)

    def visitStmt(self, n):
        sss  = [self.dispatch(s) for s in n.nodes]
        return Stmt(reduce(lambda a,b: a + b, sss, []))

    def visitAdd(self, n, lhs):
        left = n.left
        right = n.right
        if name_or_reg(left) and left.name == lhs:
            return make_arith(IntAddInstr, Name(lhs), right)
        elif name_or_reg(right) and right.name == lhs:
            return make_arith(IntAddInstr, Name(lhs), left)
        else:
            return [IntMoveInstr(Register('eax'), [left]),
                    IntAddInstr(Register('eax'), [right]),
                    IntMoveInstr(Name(lhs), [Register('eax')])]

    def visitUnarySub(self, n, lhs):
        return [IntMoveInstr(Register('eax'), [n.expr]),
                IntNegInstr(Register('eax'), []),
                IntMoveInstr(Name(lhs), [Register('eax')])]

    def visitName(self, n, lhs):
        if lhs == n.name:
            return []
        else:
            return make_arith(IntMoveInstr, Name(lhs), n)
        
    def visitConst(self, n, lhs):
        return [IntMoveInstr(Name(lhs), [n])]

    def visitCallFunc(self, n, lhs):
        push_args = [Push(a) for a in reversed(n.args)]
        # Align stack to 16-bytes for MacOS X
        align = 4 * ((4 - len(n.args)) % 4)
        pop_amount = (4 * len(n.args)) + align
        if align != 0:
            push_args = [IntSubInstr(Register('esp'), [Const(align)])] + push_args 
        if 0 < pop_amount:
            pop = [Pop(pop_amount)]
        else:
            pop = []
        return push_args + [CallX86(n.node.name)] + pop \
               + [IntMoveInstr(Name(lhs), [Register('eax')])]

    def visitAssign(self, n):
        lhs = n.nodes[0].name
        return self.dispatch(n.expr, lhs)

    def visitPrintnl(self, n):
        push_args = [Push(n.nodes[0])]
        # Align stack to 16-bytes for MacOS X
        n_args = 1
        align = 4 * ((4 - n_args) % 4)
        if align != 0:
            push_args = [IntSubInstr(Register('esp'), [Const(align)])] + push_args 
        pop_amount = (4 * n_args) + align
        if 0 < pop_amount:
            pop = [Pop(pop_amount)]
        else:
            pop = []
        return push_args + [CallX86('print_int_nl')] + pop



