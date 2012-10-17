from ir1 import *
from vis import Visitor
from compiler_utilities import generate_name

# Flatten expressions to 3-address instructions (Remove Complex Opera*)

# Input: an AST for P_1
# Output: an AST for P_1 (put without complex opera*)

# Notes: this introduces too many variables and moves, but that's OK.
# Register allocation with move biasing will hopefully take care of it.

def make_assign(lhs, rhs):
    return Assign(nodes=[AssName(name=lhs, flags='OP_ASSIGN')], expr=rhs)

class FlattenVisitor(Visitor):
    def visitModule(self, n):
        ss = self.dispatch(n.node)
        return Module(n.doc, Stmt(ss))

    # For statements: takes a statement and returns a list of instructions

    def visitStmt(self, n):
        sss  = [self.dispatch(s) for s in n.nodes]
        return reduce(lambda a,b: a + b, sss, [])

    def visitPrintnl(self, n):
        (e,ss) = self.dispatch(n.nodes[0], True)
        return ss + [Printnl([e], n.dest)]

    def visitAssign(self, n):
        lhs = n.nodes[0].name
        (rhs,ss) = self.dispatch(n.expr, False)
        return ss + [Assign(n.nodes, rhs)]

    def visitDiscard(self, n):
        (e, ss) = self.dispatch(n.expr, True)
        return ss

    # For expressions: takes an expression and a bool saying whether the
    # expression needs to be simple, and returns an expression
    # (a Name or Const if it needs to be simple) and a list of instructions.

    def visitConst(self, n, needs_to_be_simple):
        return (n, [])

    def visitName(self, n, needs_to_be_simple):
        return (n, [])

    def visitAdd(self, n, needs_to_be_simple):
        (left, ss1) = self.dispatch(n.left, True)
        (right, ss2) = self.dispatch(n.right, True)
        if needs_to_be_simple:
            tmp = generate_name('tmp')
            return (Name(tmp), ss1 + ss2 + [make_assign(tmp, Add((left, right)))])
        else:
            return (Add((left, right)), ss1 + ss2)            

    def visitUnarySub(self, n, needs_to_be_simple):
        (expr,ss) = self.dispatch(n.expr, True)
        if needs_to_be_simple:
            tmp = generate_name('tmp')
            return (Name(tmp), ss + [make_assign(tmp, UnarySub(expr))])
        else:
            return (UnarySub(expr), ss)

    def visitCallFunc(self, n, needs_to_be_simple):
        if isinstance(n.node, Name):
            args_sss = [self.dispatch(arg, True) for arg in n.args]
            args = [arg for (arg,ss) in args_sss]
            ss = reduce(lambda a,b: a + b, [ss for (arg,ss) in args_sss], [])
            if needs_to_be_simple:
                tmp = generate_name('tmp')
                return (Name(tmp), ss + [make_assign(tmp, CallFunc(n.node, args))])
            else:
                return (CallFunc(n.node, args), ss)
        else:
            raise Exception('flatten1: only calls to named functions allowed')
