from ir import *
from vis import Visitor
from compiler_utilities import generate_name
import sys
import compiler
from compiler.ast import *
from compiler_utilities import *
from closure_conversion import IndirectCallFunc, FunName

from explicit import *

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


# introduces If statements
# removes IfExp and Let expressions

class FlattenVisitor2(FlattenVisitor):

    # additional Python AST nodes
    
    def visitIfExp(self, n, needs_to_be_simple):
        (test, test_ss) = self.dispatch(n.test, True)
        (then, then_ss) = self.dispatch(n.then, True)
        (else_, else_ss) = self.dispatch(n.else_, True)        
        tmp = generate_name('tmp')
        return (Name(tmp), test_ss + [If([(test, Stmt(then_ss + [make_assign(tmp, then)]))],
                                         Stmt(else_ss + [make_assign(tmp, else_)]))])

    def visitCompare(self, n, needs_to_be_simple):
        (left,ss1) = self.dispatch(n.expr, True)
        op = n.ops[0][0]
        (right,ss2) = self.dispatch(n.ops[0][1], True)
        compare = Compare(expr=left, ops=[(op,right)])
        if needs_to_be_simple:
            tmp = generate_name('tmp')
            return (Name(tmp), ss1 + ss2 + [make_assign(tmp, compare)])
        else:
            return (compare, ss1 + ss2)            

    def visitSubscript(self, n, needs_to_be_simple):
        (c_result, c_ss) = self.dispatch(n.expr, True)
        (k_result, k_ss) = self.dispatch(n.subs[0], True)
        rhs = Subscript(expr=c_result, flags=n.flags, subs=[k_result])
        if needs_to_be_simple:
            tmp = generate_name('tmp')
            return (Name(tmp), c_ss + k_ss + [make_assign(tmp, rhs)])
        else:
            return (rhs, c_ss + k_ss)            

    # Made-up AST nodes

    def visitGetTag(self, n, needs_to_be_simple):
        (e, ss) = self.dispatch(n.arg, True)
        tmp = generate_name('tmp')
        rhs = GetTag(e)
        return (Name(tmp), ss + [make_assign(tmp, rhs)])

    def visitInjectFrom(self, n, needs_to_be_simple):
        (arg, ss) = self.dispatch(n.arg, True)
        tmp = generate_name('tmp')
        rhs = InjectFrom(n.typ, arg)
        return (Name(tmp), ss + [make_assign(tmp, rhs)])

    def visitProjectTo(self, n, needs_to_be_simple):
        (arg, ss) = self.dispatch(n.arg, True)
        tmp = generate_name('tmp')
        rhs = ProjectTo(n.typ, arg)
        return (Name(tmp), ss + [make_assign(tmp, rhs)])

    def visitLet(self, n, needs_to_be_simple):
        (rhs_result, rhs_ss) = self.dispatch(n.rhs, False)
        (body_result, body_ss) = self.dispatch(n.body, True)
        return (body_result, rhs_ss + [make_assign(n.var, rhs_result)] + body_ss)

    def visitSetSubscript(self, n, needs_to_be_simple):
        (c_result, c_ss) = self.dispatch(n.container, True)
        (k_result, k_ss) = self.dispatch(n.key, True)
        (v_result, v_ss) = self.dispatch(n.val, True)
        tmp = generate_name('tmp')
        rhs = SetSubscript(c_result, k_result, v_result)
        return (Name(tmp), c_ss + k_ss + v_ss + [make_assign(tmp, rhs)])
        

    # bonus
    def visitIf(self, n):
        (cond, thn) = n.tests[0]
        (c, c_ss) = self.dispatch(cond, True)
        thn_ss = self.dispatch(thn)
        els_ss = self.dispatch(n.else_)
        return c_ss + [If([(c, Stmt(thn_ss))], Stmt(els_ss))]
            


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

