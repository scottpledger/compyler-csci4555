from generate_x86_1 import fun_prefix
from generate_x86_2 import GenX86Visitor2
from register_alloc3 import AssignedVars3
from instruction_selection4 import StackLoc
from compiler_utilities import *
from compiler.ast import Name

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


