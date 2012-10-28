from print_visitor2 import PrintVisitor2

class PrintVisitor3(PrintVisitor2):

    def visitFunName(self, n):
        return 'fun_' + n.name

    def visitFunction(self, n):
        params = ', '.join(n.argnames)
        return 'def %s(%s):\n%s\n' % (n.name, params, self.dispatch(n.code))

    def visitReturn(self, n):
        return 'return %s' % self.dispatch(n.value)

    def visitGoto(self, n):
        return 'goto %s' % n.target_l

    def visitStackLoc(self, n):
        return '%d(%%ebp)' % n.offset

    def visitPopValue(self, n):
        return 'popl %s' % n.target

    def visitIndirectCallX86(self, n):
        return 'call *%s' % self.dispatch(n.funptr)
