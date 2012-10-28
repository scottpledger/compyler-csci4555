from generate_x86_1 import GenX86Visitor

class GenX86Visitor2(GenX86Visitor):

    def visitShiftLeftInstr(self, n):
        return '\tsall %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitShiftRightInstr(self, n):
        return '\tsarl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitIntOrInstr(self, n):
        return '\torl %s, %s' % (self.dispatch(n.rhs[0]),\
                                 self.dispatch(n.lhs))

    def visitIntAndInstr(self, n):
        return '\tandl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitCMPLInstr(self, n):
        return '\tcmpl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.rhs[1]))

    def visitSetIfEqInstr(self, n):
        return '\tsete %s' % self.dispatch(n.lhs)

    def visitSetIfNotEqInstr(self, n):
        return '\tsetne %s' % self.dispatch(n.lhs)

    def visitIntMoveZeroExtendInstr(self, n):
        return '\tmovzbl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitJumpEqInstr(self, n):
        return '\tje label_%s' % n.dest

    def visitGoto(self, n):
        return '\tjmp label_%s' % n.target_l

    def visitLabel(self, n):
        return 'label_' + n.name + ':'

    def visitIntNotInstr(self, n):
        return '\tnotl %s' % self.dispatch(n.lhs)
