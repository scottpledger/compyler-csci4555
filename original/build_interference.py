# Build Interference Graph

# Input: an AST for IR_x86
# Output: interference graph and move graph

from ir_x86 import *
from vis import Visitor
from print_visitor import PrintVisitor
from assigned_vars import AssignedVars, full_reg
from ir1 import FunName
import sys

debug = False

# only need to consider simple expressions
# use visitor for this? Let's wait and see.
def free_vars(n):
    if isinstance(n, Const):
        return set([])
    elif isinstance(n, Name):
        return set([n.name])
    elif isinstance(n, FunName):
        return set([])
    elif isinstance(n, Register): #?? -JGS
        return set([full_reg(n.name)])
    else:
        return set([])

class ModifyLiveVisitor(Visitor):

    # lhs += rhs
    def visitIntAddInstr(self, n, live):
        n.live = live
        return live | free_vars(n.lhs) | free_vars(n.rhs[0])

    # lhs -= rhs
    def visitIntSubInstr(self, n, live):
        n.live = live
        return live | free_vars(n.lhs) | free_vars(n.rhs[0])

    # lhs = -lhs
    def visitIntNegInstr(self, n, live):
        n.live = live
        return live | free_vars(n.lhs)

    # lhs = rhs
    def visitIntMoveInstr(self, n, live):
        n.live = live
        return (live - free_vars(n.lhs)) | free_vars(n.rhs[0])

    def visitCallX86(self, n, live):
        n.live = live
        return live

    def visitPush(self, n, live):
        n.live = live
        return live | free_vars(n.arg)

    def visitPop(self, n, live):
        n.live = live
        return live

    def visitPopValue(self, n, live):
        n.live = live
        return live - free_vars(n.target)
    
    def visitStmt(self, n, live):
        n.live = live
        for s in reversed(n.nodes):
            if debug:
                print live
                print s
            live = self.dispatch(s, live)

    def visitModule(self, n):
        self.dispatch(n.node, set([]))
        

class BuildInterferenceVisitor(Visitor):

    def __init__(self, registers):
        Visitor.__init__(self)
        self.interference_graph = {}
        self.move_graph = {}
        self.registers = registers

    # graph access methods

    def interferes_with(self, v):
        if v in self.interference_graph.keys():
            return self.interference_graph[v]
        else:
            raise Exception('inter_with: %s not in interference_graph' % v)

    def move_related(self, v):
        if v in self.move_graph.keys():
            return self.move_graph[v]
        else:
            raise Exception('%s not in move_graph' % v)

    def vertices(self):
        return self.interference_graph.keys()


    def get_color(self, real_color, c, num_registers):
        if c < num_registers:
            return real_color[c]
        else:
            return 'red'

    def print_interference(self, filename, ordering, color, real_color, num_registers):
        edges = set([])
        i = 0
        vertices_str = ""
        for v in ordering:
            vertices_str += '''"%s"[color=%s,label="%s.%s"]\n''' % \
                            (v, self.get_color(real_color, color[v], num_registers), \
                             v, repr(i))
            for u in self.interferes_with(v):
                if (v,u) not in edges:
                    edges |= set([(u,v)])
            i += 1
        edges_str = '\n'.join(['"%s" -- "%s"' % (u,v)
                               for (u,v) in edges])
        f = open(filename, 'w')
        stdout = sys.stdout
        sys.stdout = f
        print 'graph {\n%s\n%s\n}\n' % (vertices_str, edges_str)
        sys.stdout = stdout
        f.close()
    
    # visit methods

    def assigned_vars(self, n):
        return AssignedVars().preorder(n)

    def visitModule(self, n):
        # initialize the interference and move graph
        localvars = self.assigned_vars(n.node)
        for l in localvars:
            self.interference_graph[l] = set([])
            self.move_graph[l] = set([])
        for l in self.registers:
            self.interference_graph[l] = set([])
            self.move_graph[l] = set([])
        self.dispatch(n.node)


    def visitStmt(self, n):
        for s in reversed(n.nodes):
            self.dispatch(s)

    def default(self, n):
        if False:
            print 'visiting ' + repr(n)
        if isinstance(n, ArithInstr):
            if n.lhs:
                lhs = n.lhs.name
            else:
                lhs = None
            if isinstance(n, IntMoveInstr) \
                   and (isinstance(n.rhs[0], Name) \
                        or isinstance(n.rhs[0], Register)):
                rhs = n.rhs[0].name
                for v in n.live:
                    if lhs and v != full_reg(lhs) and v != rhs:
                        self.add_interference(v, full_reg(lhs))
                self.add_move(full_reg(lhs), rhs)
            else:
                for v in n.live:
                    if lhs and v != full_reg(lhs):
                        self.add_interference(v, full_reg(lhs))
        else:
            Visitor.default(self, n)

        
    def visitCallX86(self, n):
        # The live variables interfere with the caller-save registers.
        for v in n.live:
            # The if's are for running with reduced register sets
            if 'eax' in self.vertices():
                self.add_interference(v, 'eax')
            if 'ecx' in self.vertices():
                self.add_interference(v, 'ecx')
            if 'edx' in self.vertices():
                self.add_interference(v, 'edx')
    
    def visitPush(self, n):
        pass

    def visitPop(self, n):
        pass

    def visitPopValue(self, n):
        lhs = n.target.name
        for v in n.live:
            if lhs and v != full_reg(lhs):
                self.add_interference(v, full_reg(lhs))

    # internal methods

    def add_interference(self, v1, v2):
        if debug:
            print repr(v1) + ' interferes with ' + repr(v2)
        #if v1 in self.interference_graph.keys():
        self.interference_graph[v1] |= set([v2])
        #if v2 in self.interference_graph.keys():
        self.interference_graph[v2] |= set([v1])

    def add_move(self, v1, v2):
        if debug:
            print repr(v1) + ' move related to ' + repr(v2)
        #if v1 in self.move_graph.keys():
        self.move_graph[v1] |= set([v2])
        #if v2 in self.move_graph.keys():
        self.move_graph[v2] |= set([v1])

