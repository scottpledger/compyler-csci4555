from vis import Visitor
from compiler_utilities import *
from explicate import letify,ExplicateVisitor2
from explicit import *
from free_vars import FreeVarsVisitor
from find_locals import FindLocalsVisitor
from ir import FunName, IndirectCallFunc

class ClosureConversionVisitor(Visitor):

    def visitName(self, n):
        if n.name in builtin_functions:
            return (FunName(n.name), [])
        else:
            return (n, [])

    def visitConst(self, n):
        return (n, [])

    def visitAdd(self, n):
        (left, fs1) = self.dispatch(n.left)
        (right, fs2) = self.dispatch(n.right)
        return (Add((left, right)), fs1 + fs2)

    def visitUnarySub(self, n):
        (expr, fs) = self.dispatch(n.expr)
        return (UnarySub(expr), fs)

    def visitCallFunc(self, n):
        args_fs = [self.dispatch(arg) for arg in n.args]
        args = [arg for (arg,ss) in args_fs]
        fs1 = reduce(lambda x,y: x + y, [fs for (arg,fs) in args_fs], [])
        (node, fs2) = self.dispatch(n.node)

        if isinstance(node, FunName) and node.name in builtin_functions:
            return (CallFunc(node, args), fs1 + fs2)
        else:
            return (letify(node, lambda fun_expr:
                           IndirectCallFunc(CallFunc(FunName('get_fun_ptr'), [fun_expr]),
                                            [CallFunc(FunName('get_free_vars'), [fun_expr])]
                                            + args)),
                fs1 + fs2)

    def visitLambda(self, n):
        (code, fs) = self.dispatch(n.code)
        local_vars = FindLocalsVisitor().preorder(n.code)
        fvs = FreeVarsVisitor().preorder(n.code) - set(n.argnames) - local_vars
        fun_name = generate_label('lambda')
        fvs_var = generate_name('free_vars')
        fvs_inits = []
        i = 0
        for fv in fvs:
            fvs_inits += [Assign([AssName(fv, 'OP_ASSIGN')],
                                 Subscript(Name(fvs_var), None,
                                           [InjectFrom('int', Const(i))]))]
            i += 1
        body = Stmt(fvs_inits + code.nodes)
        func = Function(None, fun_name, [fvs_var] + n.argnames, None, 0, None, body)
        
        fvs_list = ExplicateVisitor2().preorder(List([Name(fv) for fv in fvs]))
        (fvs_list, fs2) = self.dispatch(fvs_list)
        closure = InjectFrom('big', CallFunc(FunName('create_closure'), [FunName(fun_name), fvs_list]))
        return (closure, fs + [func])

    def visitIfExp(self, n):
        (test, fs1) = self.dispatch(n.test)
        (then, fs2) = self.dispatch(n.then)
        (else_, fs3) = self.dispatch(n.else_)
        return (IfExp(test, then, else_), fs1 + fs2 + fs3)

    def visitCompare(self, n):
        (left, fs1) = self.dispatch(n.expr)
        (right, fs2) = self.dispatch(n.ops[0][1])
        return (Compare(left, [(n.ops[0][0], right)]), fs1 + fs2)

    def visitSubscript(self, n):
        (c, fs1) = self.dispatch(n.expr)
        (k, fs2) = self.dispatch(n.subs[0])
        return (Subscript(expr=c, flags=n.flags, subs=[k]),
                fs1 + fs2)

    def visitGetTag(self, n):
        (arg, fs) = self.dispatch(n.arg)
        return (GetTag(arg), fs)

    def visitInjectFrom(self, n):
        (arg, fs) = self.dispatch(n.arg)
        return (InjectFrom(n.typ, arg), fs)

    def visitProjectTo(self, n):
        (arg, fs) = self.dispatch(n.arg)
        return (ProjectTo(n.typ, arg), fs)

    def visitLet(self, n):
        (rhs, fs1) = self.dispatch(n.rhs)
        (body, fs2) = self.dispatch(n.body)
        return (Let(n.var, rhs, body), fs1 + fs2)

    def visitSetSubscript(self, n):
        (c, fs1) = self.dispatch(n.container)
        (k, fs2) = self.dispatch(n.key)
        (v, fs3) = self.dispatch(n.val)
        tmp = generate_name('tmp')
        return (SetSubscript(c, k, v),
                fs1 + fs2 + fs3)

    # statements
    
    def visitStmt(self, n):
        ss_fss  = [self.dispatch(s) for s in n.nodes]
        ss = [s for (s,fs) in ss_fss]
        fs = reduce(lambda a,b: a + b, [fs for (s,fs) in ss_fss], [])
        return (Stmt(ss), fs)

    def visitPrintnl(self, n):
        (e,fs) = self.dispatch(n.nodes[0])
        return (Printnl([e], n.dest), fs)

    def visitAssign(self, n):
        (rhs,fs) = self.dispatch(n.expr)
        return (Assign(n.nodes, rhs), fs)

    def visitDiscard(self, n):
        (expr, fs) = self.dispatch(n.expr)
        return (Discard(expr), fs)

#     def visitFunction(self, n):
#         (code, fs) = self.dispatch(n.code)
#         fvs = FreeVarsVisitor().preorder(n.code) - set(n.argnames)
#         fvs_var = generate_name('free_vars')
#         fvs_inits = []
#         i = 0
#         for fv in fvs:
#             fvs_inits += [Assign([AssName(fv, 'OP_ASSIGN')],
#                                  Subscript(Name(fvs_var), 'OP_APPLY',
#                                            [InjectFrom('int', Const(i))]))]
#             i += 1
#         body = Stmt(fvs_inits + code.nodes)
#         func = Function(n.decorators, n.name, [fvs_var] + n.argnames, n.defaults, \
#                         n.flags, n.doc, body)
        
#         (fvs_list,fs2) = self.dispatch(ExplicateVisitor2().preorder(List([Name(fv) for fv in fvs])))
#         (dummy_list,fs3) = self.dispatch(ExplicateVisitor2().preorder(List([])))
        
#         closure = CallFunc(FunName('create_closure'), [FunName(n.name), dummy_list])
#         return (Stmt([Assign([AssName(n.name, 'OP_ASSIGN')], closure),
#                       Discard(CallFunc(FunName('set_free_vars'), [Name(n.name), fvs_list]))]),
#                 fs + [func])
        
    def visitReturn(self, n):
        (value, fs)  = self.dispatch(n.value)
        return (Return(value), fs)

    def visitIf(self, n):
        (test, ss1) = self.dispatch(n.tests[0][0])
        (then, ss2) = self.dispatch(n.tests[0][1])
        (else_, ss3) = self.dispatch(n.else_)
        return (If([(test,then)], else_), ss1 + ss2 + ss3)

    def visitWhile(self, n):
        (test, ss1) = self.dispatch(n.test)
        (body, ss2) = self.dispatch(n.body)
        return (While(test,body, n.else_), ss1 + ss2)

    def visitModule(self, n):
        (node, fs) = self.dispatch(n.node)
        return Module(n.doc, Stmt(fs + node.nodes))
