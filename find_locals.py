from compiler.ast import *
from vis import Visitor

class FindLocalsVisitor(Visitor):

    def visitStmt(self, n):
        sss  = [self.dispatch(s) for s in n.nodes]
        return reduce(lambda a,b: a | b, sss, set([]))

    def visitPrintnl(self, n):
        return set([])

    def visitAssign(self, n):
        if isinstance(n.nodes[0], AssName):
            return set([n.nodes[0].name])
        else:
            return set([])

    def visitDiscard(self, n):
        return set([])
    
    def visitReturn(self, n):
        return set([])

    def visitFunction(self, n):
        return set([n.name])

    def visitIf(self, n):
        return self.dispatch(n.tests[0][1]) | self.dispatch(n.else_)

    def visitWhile(self, n):
        return self.dispatch(n.body)

    def visitClass(self, n):
        return set([n.name])

    def visitFunction(self, n):
        return set([n.name])
