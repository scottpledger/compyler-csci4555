###############################################################################
# Register Allocation

# Input: an AST for IR_x86
# Output: an AST for IR_x86 that uses fewer variables and more registers.

import sys
import compiler
from compiler.ast import *
from ir_x86 import *
from build_interference import BuildInterferenceVisitor, full_reg, ModifyLiveVisitor, free_vars
from vis import Visitor
from compiler_utilities import *
from print_visitor import PrintVisitor,PrintVisitor2,PrintVisitor3
from os.path import splitext
from priority_queue import PriorityQueue
import random

from assigned_vars import AssignedVars2

#from register_alloc import RegisterAlloc, IntroSpillCode, AssignRegistersVisitor, is_memory_access, spilled, unspillable, in_register, ModifyLiveVisitor2, BuildInterferenceVisitor2, RegisterAlloc2, IntroSpillCode2, AssignRegistersVisitor2


debug = False

unspillable = [[]]

reserved_registers = ['esp']
registers = ['eax', 'ebx', 'ecx', 'esi', 'edi', 'edx']
# Note, I get an infinite loop on the test P1_tests/or1.py
# when just using registers = ['eax', 'ebx' ] -Jeremy
# registers = ['eax', 'ebx' ]
real_color = ['blue', 'green', 'cyan', 'orange', \
              'brown', 'forestgreen', 'yellow']

move_bias_reg = 0
move_bias_stack = 0

def is_reg(c):
    return c < len(reserved_registers) + len(registers)

# We represent colors with natural numbers. The first k
# natural number represent the k registers available on the machine.

def choose_color(v, color, graphs):
    global move_bias_reg
    global move_bias_stack

    if debug:
        print 'coloring ' + v
    
    used_colors = set([color[u] for u in graphs.interferes_with(v) \
                       if u in color])

    if debug:
        print 'trying to pick move-related color'

    # try to pick the same register as a move-related variable
    move_rel_reg = [color[u] for u in graphs.move_related(v) \
                    if u in color and is_reg(color[u]) \
                    and not (color[u] in used_colors)]
    if 0 < len(move_rel_reg):
        move_bias_reg += 1
        return min(move_rel_reg)

    if debug:
        print 'trying to pick unused register'

    # try to pick an unused register
    unused_registers = [c for c in range(len(reserved_registers), \
                                         len(registers)) \
                        if not (c in used_colors)]
    if 0 < len(unused_registers):
        return min(unused_registers)

    if debug:
        print 'trying to pick move-related stack location'

    # try to pick the same color as a move-related variable
    move_rel_colors = [color[u] for u in graphs.move_related(v) \
                       if u in color and not color[u] in used_colors]
    if 0 < len(move_rel_colors):
        move_bias_stack += 1
        return min(move_rel_colors)

    if debug:
        print 'pick stack location'

    # pick the lowest unused color (this is what Palsberg does)
    lowest = len(reserved_registers)
    while True:
        if not (lowest in used_colors):
            break
        else:
            lowest += 1
    if debug:
        print 'finished coloring ' + v
    return lowest

spills = 0


num_unused = {}
used_registers = {}

def avail_reg_then_unspill(u, v):
    global unspillable
    global num_unused
    return (num_unused[u] > num_unused[v]) \
           or (num_unused[u] == num_unused[v] \
               and (u not in unspillable[0] and v in unspillable[0]))


def color_most_constrained_first(graphs, color):
    global spills, unspillable, num_unused, used_registers

    if debug:
        print 'starting color_most_constrained_first'
    
    for v in graphs.vertices():
        used_registers[v] = set([])
        num_unused[v] = len(registers) - len(used_registers[v])

    left = set(graphs.vertices()) - set(reserved_registers) - set(registers)
    queue = PriorityQueue(left, avail_reg_then_unspill)

    while not queue.empty():
        v = queue.pop()
        if debug:
            print 'next to color is ' + v
        if v not in color.keys():
            c = choose_color(v, color, graphs)
            color[v] = c
            if debug:
                print 'color of ' + str(v) + ' is ' + str(c)
            for u in graphs.interferes_with(v):
                #if u in graphs.vertices():
                used_registers[u] |= set([c])
                num_unused[u] = len(registers) - len(used_registers[u])
                queue.update(u)
            if not is_reg(c):
                spills += 1
# spills happen to unspillable in test2.py on schof! -Jeremy
#                 if v in unspillable[0]:
#                     raise Exception('spilled an unspillable! ' + v)
    if debug:
        print 'finished with color_most_constrained_first'
    return color

spilled = [False]

def in_register(node, color):
    if isinstance(node, Register):
        return True
    elif isinstance(node, Name):
        if node.name in color.keys():
            return color[node.name] < len(reserved_registers) + len(registers)
        else:
            raise Exception(node.name + ' not in color')
    else:
        return False

def is_memory_access(node, color):
    return not (in_register(node, color) or isinstance(node, Const))

def make_arith(color, klass, lhs, rhs):
    global spilled
    global unspillable
    
    if is_memory_access(lhs, color) and is_memory_access(rhs, color):
        spilled[0] = True
        tmp = generate_name('tmp')
        unspillable[0] = unspillable[0] + [tmp]
        return [IntMoveInstr(Name(tmp), [rhs]),
                klass(lhs, [Name(tmp)])]
    else:
        return [klass(lhs, [rhs])]


class IntroSpillCode(Visitor):
    def __init__(self, color):
        Visitor.__init__(self)
        self.color = color

    def visitModule(self, n):
        return Module(n.doc, self.dispatch(n.node))
    
    def visitStmt(self, n):
        sss  = [self.dispatch(s) for s in n.nodes]
        return Stmt(reduce(lambda a,b: a + b, sss, []))
    
    def visitCallX86(self, n):
        return [n]
    
    def visitPush(self, n):
        return [n]

    def visitPop(self, n):
        return [n]

    def visitPopValue(self, n):
        return [n]

    def visitNoneType(self, n):
        return n

    def visitIntMoveInstr(self, n):
        # don't spill for a move where lhs and rhs are the same
        lhs = n.lhs
        rhs = n.rhs[0]
        if (isinstance(lhs, Register) and isinstance(rhs, Register) \
            and self.color[lhs.name] == self.color[rhs.name]) \
            or (isinstance(lhs, Name) and isinstance(rhs, Name) \
                and self.color[lhs.name] == self.color[rhs.name]):
            return [n]
        else:
            if debug:
                print 'spilling ' + repr(n)
            return make_arith(self.color, IntMoveInstr, lhs, rhs)

    def default(self, n):
        if isinstance(n, ArithInstr):
            klass = n.__class__
            if len(n.rhs) > 0:
                return make_arith(self.color, klass, n.lhs, n.rhs[0])
            else:
                return [n]
        else:
            Visitor.default(self, n)


class AssignRegistersVisitor(Visitor):

    def __init__(self, color):
        Visitor.__init__(self)
        self.color = color

    def visitModule(self, n):
        return Module(n.doc, self.dispatch(n.node))
    
    def visitStmt(self, n):
        sss  = [self.dispatch(s) for s in n.nodes]
        return Stmt(reduce(lambda a,b: a + b, sss, []))
    
    def visitCallX86(self, n):
        return [n]
    
    def visitPush(self, n):
        return [Push(self.dispatch(n.arg))]

    def visitPop(self, n):
        return [n]

    def visitPopValue(self, n):
        return [PopValue(self.dispatch(n.target))]

    def visitConst(self, n):
        return n

    def visitName(self, n):
        nr = len(reserved_registers)
        if n.name in self.color:
            if self.color[n.name] < nr + len(registers):
                return Register(registers[self.color[n.name] - nr])
            else:
                return Name('local%d' % (self.color[n.name]))
        else:
            raise Exception('%s not assigned a color!' % n.name)

    def visitRegister(self, n):
        return n

    def visitNoneType(self, n):
        return n

    def visitIntMoveInstr(self, n):
        # drop the move if lhs and rhs are the same
        lhs = self.dispatch(n.lhs)
        rhs = self.dispatch(n.rhs[0])
        if (isinstance(lhs, Register) and isinstance(rhs, Register) \
            and lhs.name == rhs.name) \
            or (isinstance(lhs, Name) and isinstance(rhs, Name) \
                and lhs.name == rhs.name):
            return []
        else:
            return [IntMoveInstr(lhs, [rhs])]

    def default(self, n):
        if isinstance(n, ArithInstr):
            klass = n.__class__
            return [klass(self.dispatch(n.lhs),\
                          [self.dispatch(a) for a in n.rhs])]
        else:
            Visitor.default(self, n)

def position(x, ls):
    for i in range(0, len(ls)):
        if x == ls[i]:
            return i
    raise Exception('%s not in list' % repr(x))

class RegisterAlloc:

    def build_interference(self, all_registers):
        return BuildInterferenceVisitor(all_registers)

    def liveness(self):
        return ModifyLiveVisitor()

    def intro_spill_code(self, color, instrs):
        return IntroSpillCode(color).preorder(instrs)

    def assign_registers(self, color, instrs):
        return AssignRegistersVisitor(color).preorder(instrs)

    def instrs_to_string(self, instrs):
        return PrintVisitor().preorder(instrs)

    def allocate_registers(self, instrs, filename):
        global spilled, spills, reserved_registers, registers
        spilled[0] = True
        k = 0
        color = {}
        for r in reserved_registers:
            color[r] = position(r, reserved_registers)
        n = len(reserved_registers)
        for r in registers:
            color[r] = position(r, registers) + n

        while spilled[0]:
            if debug:
                print 'register allocation loop ' + repr(k)
            spilled[0] = False
            if debug:
                print 'liveness'
            live_vis = self.liveness()
            if debug:
                print PrintVisitor2().preorder(instrs)
            live_vis.preorder(instrs)
            if debug:
                print PrintVisitor().preorder(instrs)
            if debug:
                print 'building interference'
            graphs = self.build_interference(registers + reserved_registers)
            graphs.preorder(instrs)
            if debug:
                print 'finished building interference'
            spills = 0

            color = color_most_constrained_first(graphs, color)
            if debug:
                print 'finished coloring'
            if debug:
                itf_file = splitext(filename)[0] + '-' + repr(k) + '.dot'
                graphs.print_interference(itf_file, graphs.vertices(), color, real_color, len(reserved_registers) + len(registers))
                print 'color: ' + repr(color)
                print 'current assignment:'
                tmp = self.assign_registers(color, instrs)
                print self.instrs_to_string(tmp)
                print 'intro spill code'

            instrs = self.intro_spill_code(color, instrs)
            if spilled[0]:
                for v in graphs.vertices():
                    if v not in reserved_registers and v not in registers and is_reg(color[v]):
                        del color[v]
                
            k += 1
                       
        instrs =  self.assign_registers(color, instrs)
        return instrs


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
    
