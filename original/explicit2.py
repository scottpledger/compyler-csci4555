from explicit import PrintASTVisitor

class PrintASTVisitor2(PrintASTVisitor):

    def visitFunction(self, n):
        params = ', '.join(n.argnames)
        return 'def %s(%s):\n%s\n' % (n.name, params, self.dispatch(n.code))

    def visitReturn(self, n):
        return 'return %s' % self.dispatch(n.value)

    def visitFunName(self, n):
        return '`%s' % n.name

    def visitIndirectCallFunc(self, n):
        return self.dispatch(n.node) + '(|' + \
               ', '.join([self.dispatch(arg) for arg in n.args]) + '|)'

    def visitLambda(self, n):
        params = ', '.join(n.argnames)
        return 'lambda(%s) %s' % (params, self.dispatch(n.code))

    def visitNoneType(self, n):
        return '()'
