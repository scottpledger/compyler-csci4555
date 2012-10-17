from ir_x86 import *
from vis import Visitor

# The following register_parent stuff is forward looking :(
# Not really needed until later. Should instead
# make free_vars into a visitor.
register_parent = {'al' : 'eax',
                   'cl' : 'ecx'}

def full_reg(n):
    if n in register_parent.keys():
        return register_parent[n]
    else:
        return n

class AssignedVars(Visitor):

    def visitStmt(self, n):
        return reduce(lambda a,b: a | b, \
                      [self.dispatch(s) for s in n.nodes], set([]))

    def default(self, n):
        if isinstance(n, ArithInstr):
            if isinstance(n.lhs, Name):
                return set([n.lhs.name])
            elif isinstance(n.lhs, Register):
                return set([full_reg(n.lhs.name)])
            elif isinstance(n.lhs, None.__class__):
                return set([])
            else:
                raise Exception('expected Name in lhs of arith instr, not %s' % repr(n.lhs))
#                return set([])
        else:
            return set([])
            #return Visitor.default(self, n)
