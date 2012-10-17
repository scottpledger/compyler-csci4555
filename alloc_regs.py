import flattener
from interference import LivenessHandler, InterferenceHandler
from util import PriorityQueue
from asmnodes import *
from node_handler import Handler
from print_handler import PrintHandler
import pprint

debug = True

spilled = [False]

reserved_registers = [ASMReg('esp')]
registers = [ASMReg('eax'), ASMReg('ebx'), ASMReg('ecx'), ASMReg('esi'), ASMReg('edi'), ASMReg('edx')]

real_color = ['blue', 'green', 'cyan', 'orange', \
			  'brown', 'forestgreen', 'yellow']

def position(x, ls):
	for i in range(0, len(ls)):
		if x == ls[i]:
			return i
	raise Exception('%s not in list' % repr(x))


used_registers = {}
num_unused = {}

unspillable = [[]]

def is_reg(c):
	return c < len(reserved_registers) + len(registers)

def avail_reg_then_unspill(u, v):
	global unspillable
	global num_unused
	return (num_unused[u] > num_unused[v]) \
		  or (num_unused[u] == num_unused[v] \
			  and (u not in unspillable[0] and v in unspillable[0]))
			  
def choose_color(v, color, graphs):
	global move_bias_reg
	global move_bias_stack

	if debug:
		print 'coloring %r' % v
	
	used_colors = set([color[u] for u in graphs.get_interferences(v) \
					  if u in color])

	if debug:
		print 'trying to pick move-related color'

	# try to pick the same register as a move-related variable
	move_rel_reg = [color[u] for u in graphs.get_moves(v) \
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
		print 'finished coloring %r' % v
	return lowest

def color_most_constrained_first(graphs, color):
	global spills, unspillable, num_unused, used_registers

	if debug:
		print 'starting color_most_constrained_first'
	
	for v in graphs.get_vertices():
		used_registers[v] = set([])
		num_unused[v] = len(registers) - len(used_registers[v])

	left = set(graphs.get_vertices()) - set(reserved_registers) - set(registers)
	queue = PriorityQueue(left, avail_reg_then_unspill)

	while not queue.empty():
		v = queue.pop()
		if debug:
			print 'next to color is %r' % v
		if v not in color.keys():
			c = choose_color(v, color, graphs)
			color[v] = c
			if debug:
				print 'color of ' + str(v) + ' is ' + str(c)
			for u in graphs.get_interferences(v):
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

def make_arith(color, klass, lhs, rhs):
	global spilled
	global unspillable
	if is_memory_access(lhs, color) and is_memory_access(rhs, color):
		spilled[0] = True
		tmp = flattener.gen_temp()
		unspillable[0] = unspillable[0] + [tmp]
		return [ASMMove(rhs,flattener.gen_temp()),
				klass(tmp,lhs)]
	else:
		if klass==ASMNeg:
			return [ASMNeg(lhs)]
		else:
			return [klass(rhs, lhs)]

def in_register(node, color):
	if isinstance(node, ASMReg):
		return True
	elif isinstance(node, ASMVar):
		if node.name in color.keys():
			return color[node.name] < len(reserved_registers) + len(registers)
		else:
			raise Exception( repr(node) + ' not in color')
	else:
		return False

def is_memory_access(node, color):
	return not (in_register(node, color) or isinstance(node, Const))

class IntroSpillCode(Handler):
	def __init__(self, color):
		Handler.__init__(self)
		self.color = color

	def handleASMModule(self, n):
		return ASMModule( self.handle(n.node))
	
	def handleASMStmt(self, n):
		sss  = [self.handle(s) for s in n.nodes]
		return ASMStmt(reduce(lambda a,b: a + b, sss, []))
	
	def handleASMCall(self, n):
		return [n]
	
	def handleASMPush(self, n):
		return [n]

	def handleASMPop(self, n):
		return [n]

	def handleNoneType(self, n):
		return n

	def handleASMMove(self, n):
		# don't spill for a move where lhs and rhs are the same
		lhs = n.getDest()
		rhs = n.getSrc()
		if (isinstance(lhs, ASMReg) and isinstance(rhs, ASMReg) \
			and self.color[lhs] == self.color[rhs]) \
			or (isinstance(lhs, VarName) and isinstance(rhs, VarName) \
				and self.color[lhs] == self.color[rhs]):
			return [n]
		else:
			if debug:
				print 'spilling ' + repr(n)
			return make_arith(self.color, ASMMove, lhs, rhs)

	def default(self, n):
		if isinstance(n, ASMArithmetic):
			klass = n.__class__
			if n.getSrc():
				return make_arith(self.color, klass, n.getDest(), n.getSrc())
			else:
				return [n]
		else:
			Handler.default(self, n)

class AssignRegistersHandler(Handler):

	def __init__(self, color):
		Handler.__init__(self)
		self.color = color

	def handleASMModule(self, n):
		return ASMModule( self.handle(n.node))
	
	def handleASMStmt(self, n):
		for s in n.nodes:
			print repr(s)
		sss  = [self.handle(s) for s in n.nodes]
		return ASMStmt(reduce(lambda a,b: a + b, sss, []))
	
	def handleASMCall(self, n):
		return [n]
	
	def handleASMPush(self, n):
		return [ASMPush(self.handle(n.node))]

	def handleASMPop(self, n):
		return [n]

	def handleASMPopValue(self, n):
		return [PopValue(self.handle(n.target))]

	def handleASMConst(self, n):
		return n
	
	def handleVarName(self,n):
		return self.handle(ASMVar(n))
	
	def handleConst(self,n):
		return ASMConst(n.value)
	
	def handleASMVar(self, n):
		nr = len(reserved_registers)
		if n.name in self.color:
			if self.color[n.name] < nr + len(registers):
				n.loc =ASMReg(registers[self.color[n.name] - nr]) 
				return n
			else:
				n.loc = ASMVar('local%d' % (self.color[n.name]))
				return n
				
		else:
			raise Exception('%r not assigned a color!' % (n.name))

	def handleASMReg(self, n):
		return n

	def handleNoneType(self, n):
		return n

	def handleIntMoveInstr(self, n):
		# drop the move if lhs and rhs are the same
		lhs = self.handle(n.getDest())
		rhs = self.handle(n.getSrc())
		if (isinstance(lhs, ASMReg) and isinstance(rhs, ASMReg) \
			and lhs == rhs) \
			or (isinstance(lhs, ASMVar) and isinstance(rhs, ASMVar) \
				and lhs == rhs):
			return []
		else:
			return [ASMMove(lhs, rhs)]

	def default(self, n):
		if isinstance(n, ASMArithmetic):
			klass = n.__class__
			return [klass(self.handle(n.getSrc()),\
						  self.handle(n.getDest()))]
		else:
			Handler.default(self, n)

class RegisterAlloc:

	def build_interference(self, all_registers):
		return InterferenceHandler(all_registers)

	def liveness(self):
		return LivenessHandler()

	def intro_spill_code(self, color, instrs):
		return IntroSpillCode(color).preorder(instrs)
		return instrs

	def assign_registers(self, color, instrs):
		return AssignRegistersHandler(color).preorder(instrs)
		
		pass

	def instrs_to_string(self, instrs):
		#return PrintVisitor().preorder(instrs)
		return ''

	def allocate_registers(self, instrs, filename='tmp/reg_alloc'):
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
				print PrintHandler(lambda n: repr(n)+"\n"+str(n.live)).preorder(instrs)
			live_vis.preorder(instrs,set([]))
			#if debug:
				#print PrintVisitor().preorder(instrs)
			if debug:
				print 'building interference'
			graphs = self.build_interference(registers + reserved_registers)
			graphs.preorder(instrs)
			if debug:
				print 'finished building interference'
				print PrintHandler(lambda n: repr(n)+"\n"+str(n.live)).preorder(instrs)
			spills = 0

			color = color_most_constrained_first(graphs, color)
			if debug:
				print 'finished coloring'
			if debug:
				itf_file = filename + '-' + repr(k) + '.dot'
				graphs.print_interference(itf_file, graphs.get_vertices(), color, real_color, len(reserved_registers) + len(registers))
				print 'color: ' + repr(color)
				print 'current assignment:'
				tmp = self.assign_registers(color, instrs)
				print self.instrs_to_string(tmp)
				print 'intro spill code'

			instrs = self.intro_spill_code(color, instrs)
			if spilled[0]:
				for v in graphs.get_vertices():
					if v not in reserved_registers and v not in registers and is_reg(color[v]):
						del color[v]
				
			k += 1
					  
		instrs =  self.assign_registers(color, instrs)
		return instrs