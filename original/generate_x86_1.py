import sys
from ir_x86 import *
from vis import Visitor

###############################################################################
# Translate to x86

# Input: an AST for IR_x86
# Output: a string containing a program in x86 assembly 

if sys.platform == 'darwin':
    fun_prefix = '_'
else:
    fun_prefix = ''

class GenX86Visitor(Visitor):

    def __init__(self):
        Visitor.__init__(self)
        self.var_map = {}

    def visitModule(self, n):
        local_vars = assigned_vars(n.node)
        base_offset = 4
        for l in local_vars:
            self.var_map[l] = base_offset
            base_offset += 4

        base_ptr_space = 4
        local_var_space = len(local_vars) * 4
        weird_space = 4
        prologue_size = base_ptr_space + local_var_space + weird_space
        
        # Get 16 byte alignment
        m = prologue_size % 16
        stack_adjustment = (16 - m) + local_var_space
        return '''
.globl %smain
%smain:
\tpushl %%ebp
\tmovl %%esp, %%ebp
\tsubl $%d, %%esp
%s
\tmovl $0, %%eax
\tleave
\tret''' % (fun_prefix, fun_prefix, stack_adjustment, self.dispatch(n.node))

    def visitStmt(self, n):
        return '\n'.join([self.dispatch(x) for x in n.nodes])

    def visitConst(self, n):
        return '$%d' % n.value

    def visitName(self, n):
        if n.name in self.var_map.keys():
            return '-%d(%%ebp)' % self.var_map[n.name]
        else:
            raise Exception('%s not in the var map %s' % (n.name, repr(self.var_map)))
        
    def visitRegister(self, n):
        return '%%%s' % n.name

    def visitIntAddInstr(self, n):
        return '\taddl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitIntLEAInstr(self, n):
        return '\tleal (%s, %s), %s' % (self.dispatch(n.rhs[0]),\
                                        self.dispatch(n.rhs[1]),\
                                        self.dispatch(n.lhs))

    def visitIntSubInstr(self, n):
        return '\tsubl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitIntNegInstr(self, n):
        return '\tnegl %s' % self.dispatch(n.lhs)
            
    def visitIntMoveInstr(self, n):
        return '\tmovl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitCallX86(self, n):
        return '\tcall %s%s' % (fun_prefix, n.name)

    def visitPush(self, n):
        return '\tpushl %s' % self.dispatch(n.arg)

    def visitPop(self, n):
        return '\taddl $%s, %%esp' % n.bytes

    def visitPopValue(self, n):
        return '\tpopl %s' % self.dispatch(n.target)

