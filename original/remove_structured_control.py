from compiler.ast import *
from vis import Visitor
from compiler_utilities import *
from ir_x86_2 import *

class RemoveStructuredControl(Visitor):

    def visitModule(self, n):
        return Module(n.doc, Stmt(self.dispatch(n.node)))

    def visitStmt(self, n):
        sss = [self.dispatch(s) for s in n.nodes]
        return Stmt(reduce(lambda a,b: a + b, sss, []))

    def visitIf(self, n):
        test = n.tests[0][0]
        then = self.dispatch(n.tests[0][1])
        else_ = self.dispatch(n.else_)
        else_label = generate_name('else')
        end_label = generate_name('if_end')
        return [CMPLInstr(None, [Const(0), test]),
                JumpEqInstr(else_label)] + \
                [then] + \
                [Goto(end_label)] + \
                [Label(else_label)] + \
                [else_] + \
                [Label(end_label)]

    def visitWhile(self, n):
        test = n.test
        body = self.dispatch(n.body)
        start_label = generate_name('while_start')
        end_label = generate_name('while_end')
        return [Label(start_label),
                CMPLInstr(None, [Const(0), test]),
                JumpEqInstr(end_label)] + \
                [body] + \
                [Goto(start_label)] + \
                [Label(end_label)]

    def default(self, n):
        return [n]

    
