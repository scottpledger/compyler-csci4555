from ir_x86_3 import *
from ir2 import *
from instruction_selection3 import InstrSelVisitor3

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
