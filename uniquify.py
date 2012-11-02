import compiler
from compiler.ast import *
from vis import Visitor
from find_locals import FindLocalsVisitor
from compiler_utilities import *
from explicit import Let
import copy

class UniquifyVisitor(Visitor):
    def visitModule(self, n):
        local_vars = FindLocalsVisitor().preorder(n.node)
        renaming = {}
        for v in local_vars:
            renaming[v] = generate_name(v)
        return Module(n.doc, self.dispatch(n.node, renaming))

    def visitStmt(self, n, renaming):
        ss  = [self.dispatch(s,renaming) for s in n.nodes]
        return Stmt(ss)

    def visitPrintnl(self, n, renaming):
        e = self.dispatch(n.nodes[0], renaming)
        return Printnl([e], n.dest)

    def visitAssign(self, n, renaming):
        rhs = self.dispatch(n.expr, renaming)
        lhs = self.dispatch(n.nodes[0], renaming)
        return Assign([lhs], rhs, n.lineno)
        
    def visitAssName(self, n, renaming):
        return AssName(renaming[n.name], n.flags, n.lineno)

    def visitConst(self, n, renaming):
        return n

    def visitName(self, n, renaming):
        if n.name in renaming.keys():
            return Name(renaming[n.name])
        else:
            return n

    # Taking advantage of the bit representations of bool's to avoid if's.
    # Also, not doing any error checking, for example, adding an integer to a list.
    def visitAdd(self, n, renaming):
        left = self.dispatch(n.left, renaming)
        right = self.dispatch(n.right, renaming)
        return Add((left, right))
    
    def visitSub(self, n, renaming):
        left = self.dispatch(n.left, renaming)
        right = self.dispatch(UnarySub(n.right), renaming)
        return Add((left, right))
    
    # should do error checking
    def visitUnarySub(self, n, renaming):
        expr = self.dispatch(n.expr, renaming)
        return UnarySub(expr)

    def visitCallFunc(self, n, renaming):
        node = self.dispatch(n.node, renaming)
        args = [self.dispatch(a, renaming) for a in n.args]
        return CallFunc(node, args)

    def visitCompare(self, n, renaming):
        left = self.dispatch(n.expr, renaming)
        op = n.ops[0][0]
        right = self.dispatch(n.ops[0][1], renaming)
        return Compare(left, [(op,right)])

    def visitAnd(self, n, renaming):
        left = self.dispatch(n.nodes[0], renaming)
        right = self.dispatch(n.nodes[1], renaming)
        return And([left, right])


    def visitOr(self, n, renaming):
        left = self.dispatch(n.nodes[0], renaming)
        right = self.dispatch(n.nodes[1], renaming)
        return Or([left, right])

    def visitIfExp(self, n, renaming):
        test = self.dispatch(n.test, renaming)
        then = self.dispatch(n.then, renaming)
        else_ = self.dispatch(n.else_, renaming)
        return IfExp(test, then, else_)

    def visitNot(self, n, renaming):
        expr = self.dispatch(n.expr, renaming)
        return Not(expr)

    def visitDict(self, n, renaming):
        items = [(self.dispatch(k, renaming),
                  self.dispatch(e, renaming)) for (k, e) in n.items]
        return Dict(items)
    
    def visitList(self, n, renaming):
        nodes = [self.dispatch(e, renaming) for e in n.nodes]
        return List(nodes)

    def visitSubscript(self, n, renaming):
        expr = self.dispatch(n.expr, renaming)
        subs = [self.dispatch(e, renaming) for e in n.subs]
        return Subscript(expr, n.flags, subs)

    def visitDiscard(self, n, renaming):
        e = self.dispatch(n.expr, renaming)
        return Discard(e)

    def visitFunction(self, n, renaming):
        new_renaming = copy.deepcopy(renaming)
        local_vars = FindLocalsVisitor().preorder(n.code) | set(n.argnames)
        for v in local_vars:
            new_renaming[v] = generate_name(v)
        return Function(n.decorators, renaming[n.name],
                        [new_renaming[x] for x in n.argnames],
                        n.defaults, n.flags,
                        n.doc,
                        self.dispatch(n.code, new_renaming),
                        n.lineno)

    def visitReturn(self, n, renaming):
        return Return(self.dispatch(n.value, renaming))

    def visitLambda(self, n, renaming):
        new_renaming = copy.deepcopy(renaming)
        local_vars = n.argnames
        for v in local_vars:
            new_renaming[v] = generate_name(v)        
        return Lambda([new_renaming[x] for x in n.argnames],
                      n.defaults,
                      n.flags,
                      self.dispatch(n.code, new_renaming))

    # stuff added for hw6
    
    def visitLet(self, n, renaming):
        new_renaming = copy.deepcopy(renaming)
        new_renaming[n.var] = generate_name(n.var)
        return Let(new_renaming[n.var], self.dispatch(n.rhs, renaming),
                   self.dispatch(n.body, new_renaming))


    def visitIf(self, n, renaming):
        test = self.dispatch(n.tests[0][0], renaming)
        then = self.dispatch(n.tests[0][1], renaming)
        else_ = self.dispatch(n.else_, renaming)
        return If([(test, then)], else_)

    def visitWhile(self, n, renaming):
        test = self.dispatch(n.test, renaming)
        body = self.dispatch(n.body, renaming)
        return While(test, body, n.else_)
        
