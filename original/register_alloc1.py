###############################################################################
# Register Allocation

# Input: an AST for IR_x86
# Output: an AST for IR_x86 that uses fewer variables and more registers.

import sys
import compiler
from compiler.ast import *
from ir_x86 import *
from build_interference import BuildInterferenceVisitor, full_reg, ModifyLiveVisitor
from vis import Visitor
from compiler_utilities import *
from print_visitor import PrintVisitor
from print_visitor2 import PrintVisitor2
from os.path import splitext
from priority_queue import PriorityQueue
import random

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
