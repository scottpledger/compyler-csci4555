from ir_x86_2 import *
from ir2 import *
from instruction_selection2 import InstrSelVisitor2
from compiler_utilities import *

# Align stack to 16-bytes for MacOS X
# Should use substraction instead of repeated pushes. -Jeremy
def align_call(push_args):
    if len(push_args) % 4 != 0:
        n = 4 - (len(push_args) % 4)
        for i in range(0,n):
            push_args = [Push(Const(0))] + push_args 
    return push_args

class InstrSelVisitor3(InstrSelVisitor2):

    def visitIf(self, n):
        test = n.tests[0][0]
        then = self.dispatch(n.tests[0][1])
        return [If([(test,then)], 
                   self.dispatch(n.else_))]

    def visitWhile(self, n):
        test = n.test
        body = self.dispatch(n.body)
        return [While(test, body, n.else_)]

    # Using eax! ('al' is part of 'eax') Must keep eax in reserve!
    def visitCompare(self, n, lhs):
        left = n.expr
        op = n.ops[0][0]
        right = n.ops[0][1]
        if op == '==' or op == 'is':
            return [CMPLInstr(None, [left, right]),
                    SetIfEqInstr(Register('al')),
                    IntMoveZeroExtendInstr(Name(lhs), [Register('al')])]
        elif op == '!=':
            return [CMPLInstr(None, [left, right]),
                    SetIfNotEqInstr(Register('al')),
                    IntMoveZeroExtendInstr(Name(lhs), [Register('al')])]
        else:
            raise Exception('unhandled comparison operator: %s' % op)

    def visitSubscript(self, n, lhs):
        push_args = [Push(n.subs[0]), Push(n.expr)]
        push_args = align_call(push_args)
        return push_args + [CallX86('get_subscript'),
                            Pop(4 * len(push_args)),
                            IntMoveInstr(Name(lhs), [Register('eax')])]


    def visitGetTag(self, n, lhs):
        # lhs = n.arg & mask
        return [IntMoveInstr(Name(lhs), [n.arg]),
                IntAndInstr(Name(lhs), [Const(mask)])]

    def visitInjectFrom(self, n, lhs):
        if n.typ == 'big':
            # For pointers to big stuff, do the following
            # lhs = n.arg
            # lhs |= BIG_TAG
            return [IntMoveInstr(Name(lhs), [n.arg]),
                    IntOrInstr(Name(lhs), [Const(tag['big'])])]
        else:
            # For int and bool, do the following
            # lhs = n.arg << shift[n.typ]
            # lhs |= tag[n.typ]
            return [IntMoveInstr(Name(lhs), [n.arg]),
                    ShiftLeftInstr(Name(lhs), [Const(shift[n.typ])]),
                    IntOrInstr(Name(lhs), [Const(tag[n.typ])])]

    def visitProjectTo(self, n, lhs):
        if n.typ == 'big':
            # n.arg & ~MASK
            return [IntMoveInstr(Name(lhs), [Const(mask)]),
                    IntNotInstr(Name(lhs), []),
                    IntAndInstr(Name(lhs), [n.arg])]
        else:
            return [IntMoveInstr(Name(lhs), [n.arg]),
                    ShiftRightInstr(Name(lhs), [Const(shift[n.typ])])]

    def visitSetSubscript(self, n, lhs):
        push_args = [Push(n.val), Push(n.key), Push(n.container)]
        push_args = align_call(push_args)
        return push_args + [CallX86('set_subscript'),
                            Pop(4 * len(push_args)),
                            IntMoveInstr(Name(lhs), [Register('eax')])]


    def visitPrintnl(self, n):
        push_args = [Push(n.nodes[0])]
        push_args = align_call(push_args)
        pop = [Pop(4 * len(push_args))]
        return push_args + [CallX86('print_any')] + pop
