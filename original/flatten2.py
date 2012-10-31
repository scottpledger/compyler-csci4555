from explicit import *
from flatten1 import FlattenVisitor, make_assign
from compiler_utilities import *

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
            
