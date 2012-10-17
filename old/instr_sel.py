
from node_handler import Handler
from asmnodes import *

def make_asm_variable(n):
	if isinstance(n,VarName):
		return ASMVar(n)
	else:
		return n

def make_arithmetic_node(nclass,lhs,rhs):
	if isinstance(lhs, VarName) and isinstance(rhs,VarName):
		return [ASMMove(make_asm_variable(rhs),ASMReg('eax')),nclass(make_asm_variable(lhs),ASMReg('eax'))]
	else:
		lhs = make_asm_variable(lhs)
		rhs = make_asm_variable(rhs)
		return [nclass(rhs,lhs)]

def is_name_or_reg(n):
	return isinstance(n,VarName) or isinstance(n,ASMReg) or isinstance(n,ASMVar)

class InstrSelHandler(Handler):
	def handleModule(self,n):
		#print "Found Module!  %r"%n
		instrs = self.handle(n.node)
		
		#for c in n.node:
		#	instrs += self.handle(c)
		return ASMModule(instrs)
		
	def handleStmt(self,n):
		#print "Found Stmt!"
		stmts = []
		for m in n.nodes:
			stmts = stmts + self.handle(m)
		return [ASMStmt(stmts,n)]
	
	def handleDiscard(self,n):
		return self.handle(n.expr)
		
	def handleAssign(self,n):
		lhs = make_asm_variable(n.nodes)
		return self.handle(n.expr, lhs)

	def handleAdd(self,n,lhs):
		left = n.left
		right = n.right
		lhs_n  = make_asm_variable(lhs)
		left_n = make_asm_variable(n.left)
		right_n = make_asm_variable(n.right)
		
		if is_name_or_reg(left) and left.name == lhs.name:
			return make_arithmetic_node(ASMAdd,right_n,lhs_n)
		elif is_name_or_reg(right) and right.name == lhs.name:
			return make_arithmetic_node(ASMAdd,left_n,lhs_n)
		else:
			return [ASMMove(left_n,ASMReg('eax')),ASMAdd(right_n,ASMReg('eax')),ASMMove(ASMReg('eax'),lhs_n)]
		
	def handleConst(self,n,lhs):
		return [ASMMove(ASMConst(n.value),make_asm_variable(lhs))]
	
	def handleVarName(self,n,lhs):
		if lhs == n:
			return []
		else:
			return make_arithmetic_node(ASMMove,make_asm_variable(lhs),make_asm_variable(n))
	
	def handleCallFunc(self,n,lhs):
		lhs = make_asm_variable(lhs)
		push_args = [ASMPush(c) for c in reversed(n.args)]
		align = 4 * ((4 - len(n.args))%4)
		pop_amt = (4*len(n.args))+align
		
		if align!=0:
			push_args = [ASMSub(ASMConst(align),ASMReg('esp'))] + push_args
		
		pop = []
		if 0 < pop_amt:
			pop = ASMPop[(pop_amt)]
		
		return push_args + [ASMCall(ASMLabel(n.node.name))] + pop + [ASMMove(ASMReg('eax'),lhs)]

	def handleUnarySub(self,n,lhs):
		return [ASMMove(make_asm_variable(n.expr),ASMReg('eax')),ASMNeg(ASMReg('eax')),ASMMove(ASMReg('eax'),make_asm_variable(lhs))]
	
	def handlePrintnl(self,n):
		push_args = [ASMPush(make_asm_variable(n.nodes[0]))]
		n_args = 1
		align = 4 * ((4 - n_args)%4)
		pop_amt = (4*n_args) + align
		
		if align != 0:
			push_args = [ASMSub(ASMConst(align),ASMReg('esp'))]+push_args
		
		pop = []
		if 0 < pop_amt:
			pop = [ASMPop(pop_amt)]
		
		return push_args + [ASMCall(ASMLabel('print_int_nl'))] + pop
		
		

