from ir_x86 import *
from instruction_selection1 import InstrSelVisitor, name_or_reg

def make_arith(klass, lhs, rhs):
    return [klass(lhs, [rhs])]

class InstrSelVisitor2(InstrSelVisitor):

    def visitAdd(self, n, lhs):
        left = n.left
        right = n.right
        if name_or_reg(left) and left.name == lhs:
            return make_arith(IntAddInstr, Name(lhs), right)
        elif name_or_reg(right) and right.name == lhs:
            return make_arith(IntAddInstr, Name(lhs), left)
# LEA isn't working. -Jeremy
#         elif name_or_reg(left) and name_or_reg(right):
#             return [IntLEAInstr(Name(lhs), [left, right])]
        else:
            return make_arith(IntMoveInstr, Name(lhs), left) + \
                   make_arith(IntAddInstr, Name(lhs), right)

    def visitUnarySub(self, n, lhs):
        return make_arith(IntMoveInstr, Name(lhs), n.expr) + \
               [IntNegInstr(Name(lhs), [])]

    def visitName(self, n, lhs):
        if lhs == n.name:
            return []
        else:
            return make_arith(IntMoveInstr, Name(lhs), n)
