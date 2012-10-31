###############################################################################
# Instruction Selection
# This is a very naive version (easy to implement)

# Some of the code is more general than it needs to be for P_0.

# Input: an AST for P_1
# Output: an AST for IR_x86

from ir_x86 import *
from vis import Visitor

from ir import *
from compiler_utilities import *


def make_arith(klass, lhs, rhs):
    if isinstance(lhs, Name) and isinstance(rhs, Name):
        return [IntMoveInstr(Register('eax'), [rhs]),
                klass(lhs, [Register('eax')])]
    else:
        return [klass(lhs, [rhs])]

def name_or_reg(n):
    return isinstance(n, Name) or isinstance(n, Register)

class InstrSelVisitor(Visitor):

    def __init__(self):
        Visitor.__init__(self)
    
    def visitModule(self, n):
        ss = self.dispatch(n.node)
        return Module(n.doc, ss)

    def visitStmt(self, n):
        sss  = [self.dispatch(s) for s in n.nodes]
        return Stmt(reduce(lambda a,b: a + b, sss, []))

    def visitAdd(self, n, lhs):
        left = n.left
        right = n.right
        if name_or_reg(left) and left.name == lhs:
            return make_arith(IntAddInstr, Name(lhs), right)
        elif name_or_reg(right) and right.name == lhs:
            return make_arith(IntAddInstr, Name(lhs), left)
        else:
            return [IntMoveInstr(Register('eax'), [left]),
                    IntAddInstr(Register('eax'), [right]),
                    IntMoveInstr(Name(lhs), [Register('eax')])]

    def visitUnarySub(self, n, lhs):
        return [IntMoveInstr(Register('eax'), [n.expr]),
                IntNegInstr(Register('eax'), []),
                IntMoveInstr(Name(lhs), [Register('eax')])]

    def visitName(self, n, lhs):
        if lhs == n.name:
            return []
        else:
            return make_arith(IntMoveInstr, Name(lhs), n)
        
    def visitConst(self, n, lhs):
        return [IntMoveInstr(Name(lhs), [n])]

    def visitCallFunc(self, n, lhs):
        push_args = [Push(a) for a in reversed(n.args)]
        # Align stack to 16-bytes for MacOS X
        align = 4 * ((4 - len(n.args)) % 4)
        pop_amount = (4 * len(n.args)) + align
        if align != 0:
            push_args = [IntSubInstr(Register('esp'), [Const(align)])] + push_args 
        if 0 < pop_amount:
            pop = [Pop(pop_amount)]
        else:
            pop = []
        return push_args + [CallX86(n.node.name)] + pop \
               + [IntMoveInstr(Name(lhs), [Register('eax')])]

    def visitAssign(self, n):
        lhs = n.nodes[0].name
        return self.dispatch(n.expr, lhs)

    def visitPrintnl(self, n):
        push_args = [Push(n.nodes[0])]
        # Align stack to 16-bytes for MacOS X
        n_args = 1
        align = 4 * ((4 - n_args) % 4)
        if align != 0:
            push_args = [IntSubInstr(Register('esp'), [Const(align)])] + push_args 
        pop_amount = (4 * n_args) + align
        if 0 < pop_amount:
            pop = [Pop(pop_amount)]
        else:
            pop = []
        return push_args + [CallX86('print_int_nl')] + pop





def make_arith(klass, lhs, rhs):
    return [klass(lhs, [rhs])]

class InstrSelVisitor2(InstrSelVisitor):

    def visitAdd(self, n, lhs):
        left = n.left
        right = n.right
        if name_or_reg(left) and left.name == lhs:
            return make_arith(IntAddInstr, Name(lhs), right)
        elif name_or_reg(right) and right.name == lhs:
            return make_arith(IntAddInstr, Name(lhs), left)
# LEA isn't working. -Jeremy
#         elif name_or_reg(left) and name_or_reg(right):
#             return [IntLEAInstr(Name(lhs), [left, right])]
        else:
            return make_arith(IntMoveInstr, Name(lhs), left) + \
                   make_arith(IntAddInstr, Name(lhs), right)

    def visitUnarySub(self, n, lhs):
        return make_arith(IntMoveInstr, Name(lhs), n.expr) + \
               [IntNegInstr(Name(lhs), [])]

    def visitName(self, n, lhs):
        if lhs == n.name:
            return []
        else:
            return make_arith(IntMoveInstr, Name(lhs), n)


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


class StackLoc(Node):
    def __init__(self, offset):
        self.offset = offset

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "StackLoc(%d)" % self.offset
    
callee_saves = ['ebx', 'edx', 'esi', 'edi']

class InstrSelVisitor4(InstrSelVisitor3):

    def visitModule(self, n):
        if isinstance(n.node, Stmt):
            funs = [self.dispatch(fun) for fun in n.node.nodes if isinstance(fun, Function)]
            rest = [s for s in n.node.nodes if not isinstance(s, Function)]
            main = Function(None, "main", [], None, 0, None,
                            Stmt(rest + [Return(Const(0))]))
            main = self.dispatch(main)
            return funs + [main]
        else:
            raise Exception('in InstrSelVisitor4, expected Stmt inside Module')

    def visitFunction(self, n):
        code = self.dispatch(n.code)
        if isinstance(code, Stmt):
            # save the callee-save registers!
            push_callee_saves = [Push(Register(r)) for r in callee_saves]
            
            # load the parameters into temporary variables (hopefully registers)
            param_moves = []
            offset = 8
            for param in n.argnames:
                param_moves += [IntMoveInstr(Name(param), [StackLoc(offset)])]
                offset += 4

            return Function(n.decorators, n.name, n.argnames, n.defaults,
                            n.flags, n.doc, Stmt(push_callee_saves + param_moves + code.nodes))
        else:
            raise Exception('in InstrSelVisitor4, expected Stmt inside Function')


    def visitReturn(self, n):
        restore_callee_saves = []
        for r in reversed(callee_saves):
            restore_callee_saves += [PopValue(Register(r))]
        return restore_callee_saves + [n]

    def visitIndirectCallFunc(self, n, lhs):
        push_args = [Push(a) for a in reversed(n.args)]
        # Align stack to 16-bytes for MacOS X
        align = 4 * (4 - len(n.args) % 4)
        pop_amount = (4 * len(n.args)) + align
        if align != 0:
            push_args = [IntSubInstr(Register('esp'), [Const(align)])] + push_args 
        if 0 < pop_amount:
            pop = [Pop(pop_amount)]
        else:
            pop = []
        return push_args + [IndirectCallX86(n.node)] + pop \
               + [IntMoveInstr(Name(lhs), [Register('eax')])]

    def visitFunName(self, n, lhs):
        return [IntMoveInstr(Name(lhs), [n])]
