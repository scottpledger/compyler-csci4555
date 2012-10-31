import sys
import compiler
from compiler.ast import *
from flatten2 import FlattenVisitor2
from compiler_utilities import *
from flatten1 import make_assign
from closure_conversion import IndirectCallFunc, FunName

class FlattenVisitor3(FlattenVisitor2):

    def visitFunName(self, n, needs_to_be_simple):
        return (n, [])

    def visitFunction(self, n):
        ss = self.dispatch(n.code)
        return [Function(n.decorators, n.name, n.argnames, n.defaults, n.flags, n.doc, Stmt(ss))]

    def visitReturn(self, n):
        (e,ss) = self.dispatch(n.value, True)
        return ss + [Return(e)]

    def visitIndirectCallFunc(self, n, needs_to_be_simple):
        (node, ss1) = self.dispatch(n.node, True)
        args_sss = [self.dispatch(arg, True) for arg in n.args]
        args = [arg for (arg,ss) in args_sss]
        ss2 = reduce(lambda a,b: a + b, [ss for (arg,ss) in args_sss], [])

        if needs_to_be_simple:
            tmp = generate_name('tmp')
            return (Name(tmp), ss1 + ss2 + [make_assign(tmp, IndirectCallFunc(node, args))])
        else:
            return (IndirectCallFunc(node, args), ss1 + ss2)

    def visitCallFunc(self, n, needs_to_be_simple):
        if isinstance(n.node, FunName):
            args_sss = [self.dispatch(arg, True) for arg in n.args]
            args = [arg for (arg,ss) in args_sss]
            ss = reduce(lambda a,b: a + b, [ss for (arg,ss) in args_sss], [])
            if needs_to_be_simple:
                tmp = generate_name('tmp')
                return (Name(tmp), ss + [make_assign(tmp, CallFunc(n.node, args))])
            else:
                return (CallFunc(n.node, args), ss)
        else:
            raise Exception('flatten3: only calls to named functions allowed, not %s' % repr(n.node))
