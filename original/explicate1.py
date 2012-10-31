from explicit import *
from vis import Visitor
from compiler_utilities import *

# Make explicit the dynamic operations of Python

# Input: an AST for P_2
# Output: an AST for E_1

# argument to gen_is_true must be simple! (because it gets duplicated)
# if you try to get sneaky and ditch the compare in the else branch,
# the type checker will complain. -Jeremy
def gen_is_true(e):
    return IfExp(Compare(GetTag(e), [('==', Const(tag['big']))]),
                 CallFunc(Name('is_true'), [e]),
                 Compare(Const(0), [('!=', ProjectTo('int', e))]))

# the following is overly conservative
def pure(expr):
    return isinstance(expr, Name) or isinstance(expr, Const)

def letify(expr, k):
    if pure(expr):
        return k(expr)
    else:
        n = generate_name('letify')
        return Let(n, expr, k(Name(n)))

class ExplicateVisitor(Visitor):
    def visitModule(self, n):
        return Module(n.doc, self.dispatch(n.node))

    def visitStmt(self, n):
        ss  = [self.dispatch(s) for s in n.nodes]
        return Stmt(ss)

    def visitPrintnl(self, n):
        e = self.dispatch(n.nodes[0])
        return Printnl([e], n.dest)

    def visitAssign(self, n):
        rhs = self.dispatch(n.expr)
        lhs = n.nodes[0]
        if isinstance(lhs, AssName):
            return Assign(nodes=n.nodes, expr=rhs)
        elif isinstance(lhs, Subscript):
            c = self.dispatch(lhs.expr)
            k = self.dispatch(lhs.subs[0])
            return Discard(SetSubscript(c, k, rhs))
        else:
            raise Exception('unrecognized lhs in Assign: %s' % repr(lhs))

    def visitConst(self, n):
        if isinstance(n.value, str):
            return n
        else:
            return InjectFrom(type(n.value).__name__, n)

    def visitName(self, n):
        if n.name == 'True':
            return InjectFrom('bool', Const(True))
        elif n.name == 'False':
            return InjectFrom('bool', Const(False))
        elif n.name == 'input':
            return Name('input_int')
        else:
            return n

    # Taking advantage of the bit representations of bool's to avoid if's.
    # Also, not doing any error checking, for example, adding an integer to a list.
    def visitAdd(self, n):
        left = self.dispatch(n.left)
        right = self.dispatch(n.right)
        def result(l, r):
            return IfExp(Compare(GetTag(l), [('==', Const(tag['int']))]),
                         InjectFrom('int', Add((ProjectTo('int', l), \
                                                ProjectTo('int', r)))),
                         IfExp(Compare(GetTag(l), [('==', Const(tag['bool']))]),
                               InjectFrom('int', Add((ProjectTo('int', l), \
                                                      ProjectTo('int', r)))),
                               InjectFrom('big', CallFunc(Name('add'), [ProjectTo('big', l), ProjectTo('big', r)]))))


        return letify(left, lambda l: letify(right, lambda r: result(l, r)))

    # should do error checking
    def visitUnarySub(self, n):
        if isinstance(n.expr, Const) and (isinstance(n.expr.value, int) or
                                          isinstance(n.expr.value, long)):
            return InjectFrom('int', Const(int(- n.expr.value)))
        else:
            expr = self.dispatch(n.expr)
            return InjectFrom('int', UnarySub(ProjectTo('int', expr)))

    def visitCallFunc(self, n):
        node = self.dispatch(n.node)
        args = [self.dispatch(a) for a in n.args]
        if isinstance(node, Name) and node.name in builtin_functions:
            if return_type[node.name] == 'pyobj':
                return CallFunc(node, args)
            else:
                return InjectFrom(return_type[node.name], CallFunc(node, args))
        else:
            return CallFunc(node, args)

    def visitCompare(self, n):
        left = self.dispatch(n.expr)
        op = n.ops[0][0]
        right = self.dispatch(n.ops[0][1])
        if op == 'is':
            return InjectFrom('bool', Compare(left, [('is', right)]))
        else:
            op2fun = {'==':'equal', '!=':'not_equal'}
            def result(l, r):
                return IfExp(Compare(GetTag(l), [('==', Const(tag['int']))]),
                                 InjectFrom('bool', Compare(ProjectTo('int', l), \
                                                            [(op, ProjectTo('int', r))])),
                                 IfExp(Compare(GetTag(l), [('==', Const(tag['bool']))]),
                                       InjectFrom('bool', Compare(ProjectTo('int', l),
                                                                  [(op, ProjectTo('int', r))])),
                                       InjectFrom('bool', CallFunc(Name(op2fun[op]), [ProjectTo('big', l), ProjectTo('big', r)]))))
                
            return letify(left, lambda l: letify(right, lambda r: result(l, r)))

    def visitAnd(self, n):
        left = self.dispatch(n.nodes[0])
        right = self.dispatch(n.nodes[1])
        return letify(left, lambda l: IfExp(gen_is_true(l), right, l))


    def visitOr(self, n):
        left = self.dispatch(n.nodes[0])
        right = self.dispatch(n.nodes[1])
        return letify(left, lambda l: IfExp(gen_is_true(l), l, right))

    def visitIfExp(self, n):
        test = self.dispatch(n.test)
        then = self.dispatch(n.then)
        else_ = self.dispatch(n.else_)
        return IfExp(letify(test, lambda t: gen_is_true(t)),
                     then, else_)

    def visitNot(self, n):
        expr = self.dispatch(n.expr)
        return InjectFrom('bool', Compare(Const(0), [('==', letify(expr, lambda t: gen_is_true(t)))]))

    def visitDict(self, n):
        items = [(self.dispatch(k), self.dispatch(e)) for (k, e) in n.items]
        d = generate_name('dict')
        fill_dict = Name(d)
        for (k, v) in reversed(items):
            bogus = generate_name('_')
            fill_dict = Let(bogus, SetSubscript(Name(d), k, v), fill_dict)
        return Let(d, InjectFrom('big', CallFunc(Name('create_dict'), [])),
                   fill_dict)
    
    def visitList(self, n):
        nodes = [self.dispatch(e) for e in n.nodes]
        ls = generate_name('list')
        fill_list = Name(ls)
        i = len(nodes) - 1
        for v in reversed(nodes):
            bogus = generate_name('_')
            k = self.dispatch(Const(i))
            fill_list = Let(bogus, SetSubscript(Name(ls), k, v), fill_list)
            i = i - 1
        n = InjectFrom('int', Const(len(nodes)))
        return Let(ls, InjectFrom('big', CallFunc(Name('create_list'), [n])),
                   fill_list)

    def visitSubscript(self, n):
        expr = self.dispatch(n.expr)
        subs = [self.dispatch(e) for e in n.subs]
        return Subscript(expr, n.flags, subs)

    def visitDiscard(self, n):
        e = self.dispatch(n.expr)
        return Discard(e)

    def visitIf(self, n):
        tests = [(letify(self.dispatch(cond), lambda t: gen_is_true(t)),
                  self.dispatch(branch)) for (cond,branch) in n.tests]
        els = self.dispatch(n.else_)
        return If(tests, els)
