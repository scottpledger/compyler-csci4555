from vis import Visitor
from ir_x86 import *

def get_liveness(n):
    if not hasattr(n, 'live'):
        n.live = set([])
    return n.live
    

class GarbifyVisitor(Visitor):

    def visitModule(self, n, live_before=set([])):
        return self.dispatch(n.node)

    def visitStmt(self, n, live_before=set([])):
        return '{\n' + '\n  '.join([self.dispatch(s) + liveness(s) for s in n.nodes]) + '\n}'

    def visitCallX86(self, n, live_before=set([])):
        return 'call ' + n.name 

    def visitPush(self, n, live_before=set([])):
        return 'pushl ' + self.dispatch(n.arg) 

    def visitPop(self, n, live_before=set([])):
        return 'addl $' + repr(n.bytes) + ', %esp' 

    def visitIntMoveInstr(self, n, live_before=set([])):
        return ('movl %s, %s' % (self.dispatch(n.rhs[0]),
                                self.dispatch(n.lhs))) 

    def visitIntAddInstr(self, n, live_before=set([])):
        return ('addl %s, %s' % (self.dispatch(n.rhs[0]),
                                self.dispatch(n.lhs))) 

    def visitIntLEAInstr(self, n, live_before=set([])):
        return ('%s = %s + %s' % (self.dispatch(n.lhs),
                                 self.dispatch(n.rhs[0]),
                                 self.dispatch(n.rhs[1]))) 

    def visitIntSubInstr(self, n, live_before=set([])):
        return ('subl %s, %s' % (self.dispatch(n.rhs[0]), self.dispatch(n.lhs)
                                )) 

    def visitIntNegInstr(self, n, live_before=set([])):
        x = self.dispatch(n.lhs)
        return ('negl %s' % x)  

    def visitName(self, n, live_before=set([])):
        return n.name

    def visitRegister(self, n, live_before=set([])):
        return '%' + n.name

    def visitConst(self, n, live_before=set([])):
        return repr(n.value)

    def visitShiftLeftInstr(self, n, live_before=set([])):
        if len(n.rhs) > 1:
            return "%s = %s << %s" % (self.dispatch(n.lhs),
                                      self.dispatch(n.rhs[0]),
                                      self.dispatch(n.rhs[1]))
        else:
            return "sall %s, %s" % (self.dispatch(n.rhs[0]),
                                    self.dispatch(n.lhs))

    def visitShiftRightInstr(self, n, live_before=set([])):
        if len(n.rhs) > 1:
            return "%s = %s >> %s" % (self.dispatch(n.lhs),
                                      self.dispatch(n.rhs[0]),
                                      self.dispatch(n.rhs[1]))
        else:
            return "sarl %s, %s" % (self.dispatch(n.rhs[0]),
                                   self.dispatch(n.lhs))


    def visitIntOrInstr(self, n, live_before=set([])):
        if len(n.rhs) > 1:
            return "%s = %s | %s" % (self.dispatch(n.lhs),
                                     self.dispatch(n.rhs[0]),
                                     self.dispatch(n.rhs[1]))
        else:
            return "orl %s, %s" % (self.dispatch(n.rhs[0]),
                                  self.dispatch(n.lhs))


    def visitIntAndInstr(self, n, live_before=set([])):
        if len(n.rhs) > 1:
            return "%s = %s & %s" % (self.dispatch(n.lhs),
                                     self.dispatch(n.rhs[0]),
                                     self.dispatch(n.rhs[1]))
        else:
            return "andl %s, %s" % (self.dispatch(n.lhs),
                                 self.dispatch(n.rhs[0]))

    def visitIntNotInstr(self, n, live_before=set([])):
        x = self.dispatch(n.lhs)
        return 'negl %s' % x
    

    def visitCMPLInstr(self, n, live_before=set([])):
        return "cmpl %s, %s" % (self.dispatch(n.rhs[0]),
                                 self.dispatch(n.rhs[1]))

    def visitSetIfEqInstr(self, n, live_before=set([])):
        return "sete %s" % self.dispatch(n.lhs)

    def visitSetIfNotEqInstr(self, n, live_before=set([])):
        return "setne %s" % self.dispatch(n.lhs)

    def visitIntMoveZeroExtendInstr(self, n, live_before=set([])):
        return "movbzl %s, %s" % (','.join([self.dispatch(c) for c in n.rhs]),
                                 self.dispatch(n.lhs))

    def visitJumpEqInstr(self, n, live_before=set([])):
        return "je label_%s" % n.dest

    def visitIf(self, n, live_before=set([])):
        return "if %s then\n%s\nelse\n%s" % (self.dispatch(n.tests[0][0]),
                                             self.dispatch(n.tests[0][1]),
                                             self.dispatch(n.else_))

    def visitWhile(self, n, live_before=set([])):
        return "while %s:\n%s" % (self.dispatch(n.test),
                                  self.dispatch(n.body))

    def visitstr(self, n, live_before=set([])):
        return n
    
    def visitLabel(self, n, live_before=set([])):
        return "label_%s:" % n.name

    def visitFunName(self, n, live_before=set([])):
        return 'fun_' + n.name

    def visitFunction(self, n, live_before=set([])):
        params = ', '.join(n.argnames)
        code = self.dispatch(n.code)
        return 'def %s(%s):\n%s\n' % (n.name, params, code)

    def visitReturn(self, n, live_before=set([])):
        return 'return %s' % self.dispatch(n.value)

    def visitGoto(self, n, live_before=set([])):
        return 'goto %s' % n.target_l

    def visitStackLoc(self, n, live_before=set([])):
        return '%d(%%ebp)' % n.offset

    def visitPopValue(self, n, live_before=set([])):
        return 'popl %s' % n.target

    def visitIndirectCallX86(self, n, live_before=set([])):
        return 'call *%s' % self.dispatch(n.funptr)
