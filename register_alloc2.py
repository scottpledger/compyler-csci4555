from build_interference import BuildInterferenceVisitor, ModifyLiveVisitor, free_vars
from compiler_utilities import *
from print_visitor2 import PrintVisitor2
from assigned_vars2 import AssignedVars2
from ir_x86_2 import *
from register_alloc1 import RegisterAlloc, IntroSpillCode, AssignRegistersVisitor, \
     is_memory_access, spilled, unspillable, in_register
from vis import Visitor

debug = False

class ModifyLiveVisitor2(ModifyLiveVisitor):

    def visitLabel(self, n, live):
        n.live = live
        return n.live

    def visitIf(self, n, live):
        n.live = live
        then_live = self.dispatch(n.tests[0][1], live)
        else_live = self.dispatch(n.else_, live)
        return then_live | else_live | free_vars(n.tests[0][0])

    def visitWhile(self, n, live):
        n.live = live
        test_free = free_vars(n.test)
        body_live = self.dispatch(n.body, live | test_free)
        body_live = self.dispatch(n.body, live | test_free | body_live)
        return live | test_free | body_live

    def visitStmt(self, n, live):
        n.live = live
        for s in reversed(n.nodes):
            live = self.dispatch(s, live)
        return live

    def visitIntNotInstr(self, n, live):
        n.live = live
        return live | free_vars(n.lhs)

    def visitIntMoveZeroExtendInstr(self, n, live):
        n.live = live
        return (live - free_vars(n.lhs)) | free_vars(n.rhs[0])

    def default(self, n, live):
        n.live = live
        if isinstance(n, ArithInstr):
            return live | free_vars(n.lhs) \
                     | reduce(lambda a,b: a | b,
                              [free_vars(r) for r in n.rhs],
                              set([]))
        else:
            return Visitor.default(self, n, live)

    def visitSetIfEqInstr(self, n, live):
        n.live = live
        return live - free_vars(n.lhs)

    def visitSetIfNotEqInstr(self, n, live):
        n.live = live
        return live - free_vars(n.lhs)
    

class BuildInterferenceVisitor2(BuildInterferenceVisitor):

    def assigned_vars(self, n):
        return AssignedVars2().preorder(n)

    def visitLabel(self, n):
        pass

    def visitIf(self, n):
        self.dispatch(n.tests[0][1])
        self.dispatch(n.else_)

    def visitWhile(self, n):
        self.dispatch(n.body)

class IntroSpillCode2(IntroSpillCode):
    def visitIf(self, n):
        return [If(tests=[(n.tests[0][0],
                           self.dispatch(n.tests[0][1]))],
                   else_=self.dispatch(n.else_))]

    def visitWhile(self, n):
        return [While(n.test, self.dispatch(n.body), n.else_)]

    def visitCMPLInstr(self, n):
        global spilled
        global unspillable
        # What a pain, the right-hand operand can't be a constant!
        left = n.rhs[0]
        right = n.rhs[1]
        if not ((is_memory_access(left, self.color) and \
                is_memory_access(right, self.color)) or \
                isinstance(right, Const)):
            return [n]
        elif not isinstance(left, Const) and isinstance(right, Const):
            return [CMPLInstr(None, [right, left])]
        else:
            spilled[0] = True
            if debug:
                print 'need to introduce spill code for ' + repr(n)
            if in_register(left, self.color):
                new_left = left
                left_instr = []
            else:
                tmp = generate_name('tmp')
                unspillable[0] = unspillable[0] + [tmp]
                new_left = Name(tmp)
                left_instr = [IntMoveInstr(new_left, [left])]
                
            if is_memory_access(right, self.color):
                tmp = generate_name('tmp')
                unspillable[0] = unspillable[0] + [tmp]
                new_right = Name(tmp)
                right_instr = [IntMoveInstr(new_right, [right])]
            else:
                new_right = right
                right_instr = []

            return left_instr + right_instr + [CMPLInstr(None, [new_left, new_right])]

    def visitIntMoveZeroExtendInstr(self, n):
        global spilled
        global unspillable
        
        if in_register(n.lhs, self.color):
            return [n]
        else:
            spilled[0] = True
            if debug:
                print 'need to introduce spill code for ' + repr(n)
            tmp = generate_name('tmp')
            unspillable[0] = unspillable[0] + [tmp]
            return [IntMoveZeroExtendInstr(Name(tmp), [n.rhs[0]]),
                    IntMoveInstr(n.lhs, [Name(tmp)])]


class AssignRegistersVisitor2(AssignRegistersVisitor):

    def visitIf(self, n):
        return [If(tests=[(self.dispatch(n.tests[0][0]),
                           self.dispatch(n.tests[0][1]))],
                   else_=self.dispatch(n.else_))]

    def visitWhile(self, n):
        return [While(self.dispatch(n.test),
                      self.dispatch(n.body),
                      n.else_)]


class RegisterAlloc2(RegisterAlloc):

    def liveness(self):
        return ModifyLiveVisitor2()

    def build_interference(self, all_registers):
        return BuildInterferenceVisitor2(all_registers)

    def intro_spill_code(self, color, instrs):
        return IntroSpillCode2(color).preorder(instrs)

    def assign_registers(self, color, instrs):
        return AssignRegistersVisitor2(color).preorder(instrs)

    def instrs_to_string(self, instrs):
        return PrintVisitor2().preorder(instrs)
