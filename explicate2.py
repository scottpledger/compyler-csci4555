import sys
import compiler
from compiler.ast import *
from explicate1 import ExplicateVisitor
from explicit import InjectFrom

class ExplicateVisitor2(ExplicateVisitor):

    def visitFunction(self, n):
        # The extra Return is to prevent falling off the end of a function.
        lam = Lambda(n.argnames, n.defaults, n.flags,
                     Stmt([self.dispatch(n.code),
                           Return(InjectFrom('int', Const(0)))]))
        return Assign([AssName(n.name, 'OP_ASSIGN')], lam)

    def visitReturn(self, n):
        return Return(self.dispatch(n.value))

    def visitLambda(self, n):
        return Lambda(n.argnames, n.defaults, n.flags,
                      Stmt([Return(self.dispatch(n.code))]))
