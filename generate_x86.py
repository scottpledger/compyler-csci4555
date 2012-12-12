import sys
from ir_x86 import *
from vis import Visitor

from register_alloc import AssignedVars3
from instruction_selection import StackLoc
from compiler_utilities import *
from compiler.ast import Name

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

class GenX86Visitor2(GenX86Visitor):

    def visitShiftLeftInstr(self, n):
        return '\tsall %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitShiftRightInstr(self, n):
        return '\tsarl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitIntOrInstr(self, n):
        return '\torl %s, %s' % (self.dispatch(n.rhs[0]),\
                                 self.dispatch(n.lhs))

    def visitIntAndInstr(self, n):
        return '\tandl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitCMPLInstr(self, n):
        return '\tcmpl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.rhs[1]))

    def visitSetIfEqInstr(self, n):
        return '\tsete %s' % self.dispatch(n.lhs)

    def visitSetIfNotEqInstr(self, n):
        return '\tsetne %s' % self.dispatch(n.lhs)

    def visitIntMoveZeroExtendInstr(self, n):
        return '\tmovzbl %s, %s' % (self.dispatch(n.rhs[0]),\
                                  self.dispatch(n.lhs))

    def visitJumpEqInstr(self, n):
        return '\tje label_%s' % n.dest

    def visitGoto(self, n):
        return '\tjmp label_%s' % n.target_l

    def visitLabel(self, n):
        return 'label_' + n.name + ':'

    def visitIntNotInstr(self, n):
        return '\tnotl %s' % self.dispatch(n.lhs)


string_constants = {}

class GenX86Visitor3(GenX86Visitor2):

    def visitFunction(self, n):
        self.var_map = {}
        local_vars = AssignedVars3().preorder(n.code)
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
%s%s:
\tpushl %%ebp
\tmovl %%esp, %%ebp
\tsubl $%d, %%esp
%s
''' % (fun_prefix, n.name, stack_adjustment, self.dispatch(n.code))
        
        
    def visitReturn(self, n):
        return '''
        movl %s, %%eax
        leave
        ret''' % self.dispatch(n.value)


    def visitStackLoc(self, n):
        return '%d(%%ebp)' % n.offset
        
    def visitFunName(self, n):
        return '$%s' % fun_prefix + n.name

    def visitIndirectCallX86(self, n):
        return '\tcall *%s' % self.dispatch(n.funptr)

    def visitConst(self, n):
        if isinstance(n.value, str):
            tmp = generate_label('str')
            string_constants[tmp] = n.value
            return '$%s' % tmp
        else:
            return '$%d' % n.value

class GenX86Visitor4(GenX86Visitor3):
    def visitModule(self,n):
      x86_str = GenX86Visitor3.visitModule(self,n)
      out_str = ".DATA\n"
      for key in string_constants.keys():
        out_str += "%s DB '%s',0\n" %(key,string_constants[key])
      out_str += x86_str
      return out_str
