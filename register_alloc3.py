import compiler
from compiler.ast import *
from build_interference import free_vars
from register_alloc1 import spilled, unspillable, in_register
from register_alloc2 import ModifyLiveVisitor2, BuildInterferenceVisitor2, RegisterAlloc2, IntroSpillCode2, AssignRegistersVisitor2, in_register
from print_visitor3 import PrintVisitor3
from assigned_vars2 import AssignedVars2
from ir_x86_3 import *
from compiler_utilities import *

class ModifyLiveVisitor3(ModifyLiveVisitor2):

    def visitFunction(self, n, live = set([])):
        n.live = live
        self.dispatch(n.code, set([]))
        return live - set([n.name])

    def visitReturn(self, n, live):
        n.live = live
        return free_vars(n.value)

    def visitIndirectCallX86(self, n, live):
        n.live = live
        return live | free_vars(n.funptr)
    

class AssignedVars3(AssignedVars2):

    def visitFunction(self, n):
        return set([])

    def visitReturn(self, n):
        return set([])


class BuildInterferenceVisitor3(BuildInterferenceVisitor2):

    def assigned_vars(self, n):
        return AssignedVars3().preorder(n)

    def visitFunction(self, n):
        localvars = self.assigned_vars(n.code) | set(n.argnames)
        for l in localvars:
            self.interference_graph[l] = set([])
            self.move_graph[l] = set([])
        for l in self.registers:
            self.interference_graph[l] = set([])
            self.move_graph[l] = set([])
        self.dispatch(n.code)
        
    def visitReturn(self, n):
        pass

    def visitIndirectCallX86(self, n):
        # The live variables interfere with the caller-save registers.
        for v in n.live:
            # The if's are for running with reduced register sets
            if 'eax' in self.vertices():
                self.add_interference(v, 'eax')
            if 'ecx' in self.vertices():
                self.add_interference(v, 'ecx')
            if 'edx' in self.vertices():
                self.add_interference(v, 'edx')

class IntroSpillCode3(IntroSpillCode2):

    def __init__(self, color):
        IntroSpillCode2.__init__(self, color)

    def visitFunction(self, n):
        return Function(n.decorators, n.name, n.argnames, n.defaults,
                        n.flags, n.doc, self.dispatch(n.code))

    def visitReturn(self, n):
        return [n]

    def visitIndirectCallX86(self, n):
        return [n]


class AssignRegistersVisitor3(AssignRegistersVisitor2):
    def visitFunction(self, n):
        return Function(n.decorators, n.name, n.argnames, n.defaults,
                        n.flags, n.doc, self.dispatch(n.code))

    def visitReturn(self, n):
        return [Return(self.dispatch(n.value))]

    def visitStackLoc(self, n):
        return n

    def visitFunName(self, n):
        return n

    def visitIndirectCallX86(self, n):
        return [IndirectCallX86(self.dispatch(n.funptr))]


class RegisterAlloc3(RegisterAlloc2):

    def liveness(self):
        return ModifyLiveVisitor3()

    def build_interference(self, all_registers):
        return BuildInterferenceVisitor3(all_registers)

    def intro_spill_code(self, color, instrs):
        return IntroSpillCode3(color).preorder(instrs)

    def assign_registers(self, color, instrs):
        return AssignRegistersVisitor3(color).preorder(instrs)

    def instrs_to_string(self, instrs):
        return PrintVisitor3().preorder(instrs)
    
