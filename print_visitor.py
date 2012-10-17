from vis import Visitor
from ir_x86 import *

def liveness(n):
    if hasattr(n, 'live'):
        s = '\t{' + ','.join(n.live) + '}'
    else:
        s = ''
    return s
    

class PrintVisitor(Visitor):

    def visitModule(self, n):
        return self.dispatch(n.node)

    def visitStmt(self, n):
        return '{\n' + '\n'.join([self.dispatch(s) for s in n.nodes]) + '\n}'

    def visitCallX86(self, n):
        return 'call ' + n.name + liveness(n)

    def visitPush(self, n):
        return 'pushl ' + self.dispatch(n.arg) + liveness(n)

    def visitPop(self, n):
        return 'addl $' + repr(n.bytes) + ', %esp' + liveness(n)

    def visitIntMoveInstr(self, n):
        return ('movl %s, %s' % (self.dispatch(n.rhs[0]),
                                self.dispatch(n.lhs))) + liveness(n)

    def visitIntAddInstr(self, n):
        return ('addl %s, %s' % (self.dispatch(n.rhs[0]),
                                self.dispatch(n.lhs))) + liveness(n)

    def visitIntLEAInstr(self, n):
        return ('%s = %s + %s' % (self.dispatch(n.lhs),
                                 self.dispatch(n.rhs[0]),
                                 self.dispatch(n.rhs[1]))) + liveness(n)

    def visitIntSubInstr(self, n):
        return ('subl %s, %s' % (self.dispatch(n.rhs[0]), self.dispatch(n.lhs)
                                )) + liveness(n)

    def visitIntNegInstr(self, n):
        x = self.dispatch(n.lhs)
        return ('negl %s' % x)  + liveness(n)

    def visitName(self, n):
        return n.name

    def visitRegister(self, n):
        return '%' + n.name

    def visitConst(self, n):
        return repr(n.value)
