import sys
import compiler
from compiler.ast import *
from flatten3 import FlattenVisitor3
from compiler_utilities import *
from flatten1 import make_assign
from closure_conversion import IndirectCallFunc, FunName

class FlattenVisitor4(FlattenVisitor3):

    def visitIf(self, n):
        (test, test_ss) = self.dispatch(n.tests[0][0], True)
        then_ss = self.dispatch(n.tests[0][1])
        else_ss = self.dispatch(n.else_)
        return test_ss + [If([(test,Stmt(then_ss))], Stmt(else_ss)) ]

    def visitWhile(self, n):
        (test, test_ss) = self.dispatch(n.test, True)
        body_ss = self.dispatch(n.body)
        return test_ss + [While(test, Stmt(body_ss + test_ss), n.else_)]

