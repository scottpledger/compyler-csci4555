from node_handler import Handler
from asmnodes import *
import sys

def free_vars(n):
	if isinstance(n, ASMConst):
		return set([])
	elif isinstance(n, VarName):
		return set([n])
	elif isinstance(n, ASMReg):
		return set([n])
	else:
		return set([])


class LivenessHandler(Handler):
	def pretty_print(self, instrs):
		max_len = max([len(repr(n)) for n in instrs])
	
		for ins in instrs:
			print str("{0:"+str(max_len)+"} # {1}").format(str(ins),repr(ins.live))

	def handle(self,node,*args):
		self.node = node
		if type(node) is list:
			print "Found a list...%r"%self.__class__.__name__
			return [self.handle(n,*args) for n in reversed(node)]
		
		nclass = node.__class__
		method = self._cache.get(nclass, None)
		if method is None:
			className = nclass.__name__
			method = getattr(self.visitor, 'handle'+className,self.default)
			self._cache[nclass] = method
		return method(node,*args)
	
	def handleASMModule(self,n,live):
		n.live = self.handle(n.node,live)
		return n.live
	
	def handleASMStmt(self,n,live):
		for s in reversed(n.nodes):
		  live = self.handle(s, live)

	def handleASMAdd(self, n, live):
		n.live = live | free_vars(n.left) | free_vars(n.right)
		return n.live
	
	def handleASMSub(self,n,live):
		n.live = live | free_vars(n.left) | free_vars(n.right)
		return n.live
	
	def handleASMMove(self,n,live):
		n.live = live | free_vars(n.left) | free_vars(n.right)
		return n.live
		
	def handleASMNeg(self,n,live):
		n.live = live | free_vars(n.node)
		return n.live
	
	def handleASMCall(self,n,live):
		n.live = live
		return n.live
	
	def handleASMPush(self,n,live):
		n.live = live | free_vars(n.node)
		return n.live
	
	def handleASMPop(self,n,live):
		n.live = live
		return n.live

class AssignedVars(Handler):

	def handleStmt(self, n):
		return reduce(lambda a,b: a | b, \
					  [self.dispatch(s) for s in n.nodes], set([]))

	def default(self, n):
		if isinstance(n, ASMArithmetic):
			left = n.getDest()
			right = n.getSrc()
			if isinstance(left, ASMLoc):
				return set([left])
			elif isinstance(left, None.__class__):
				return set([])
			else:
				raise Exception('Did not expect not %r in dest of %r' % (left,n))
		else:
			return set([])


class InterferenceHandler(Handler):
	def __init__(self, registers):
		Handler.__init__(self)
		self.interference_graph = {}
		self.move_graph = {}
		self.registers = registers
	
	def handle(self,node,*args):
		self.node = node
		if type(node) is list:
			print "Found a list... %r"%self.__class__.__name__
			return [self.handle(n,*args) for n in reversed(node)]
		
		nclass = node.__class__
		method = self._cache.get(nclass, None)
		if method is None:
			class_queue = list()
			class_queue.append(nclass)
			pclass = None
			className = "None"
			while len(class_queue) > 0:
				pclass = class_queue.pop(0)
				className = pclass.__name__
				if hasattr(self.visitor, 'handle'+className):
					break
				else:
					for p in pclass.__bases__:
						class_queue.append(p)
			
			method = getattr(self.visitor, 'handle'+className,self.default)
			self._cache[nclass] = method
		return method(node,*args)
	
	def get_interferences(self, v):
		if v in self.interference_graph.keys():
			return self.interference_graph[v]
		else:
			raise Exception('%s not in interference_graph' % v)
			return set([])
	
	def get_moves(self, v):
		if v in self.move_graph.keys():
			return self.move_graph[v]
		else:
			#raise Exception('%s not in move_graph: %r' % (v,self.move_graph)) #TODO: There seems to be a bug concerning this but I have no idea what it is.
			return set([])
	
	def get_vertices(self):
		return self.interference_graph.keys()
	
	def assigned_vars(self,n):
		return AssignedVars().preorder(n)
	
	def add_interference(self, v1, v2):
		if v1 not in self.interference_graph:
			self.interference_graph[v1] = set([])
		if v2 not in self.interference_graph:
			self.interference_graph[v2] = set([])
		self.interference_graph[v1] |= set([v2])
		self.interference_graph[v2] |= set([v1])

	def add_move(self, v1, v2):
		if v1 not in self.move_graph:
			self.move_graph[v1] = set([])
		if v2 not in self.move_graph:
			self.move_graph[v2] = set([])
		self.move_graph[v1] |= set([v2])
		self.move_graph[v2] |= set([v1])
	
	def handleASMModule(self,n):
		localvars = self.assigned_vars(n.node[0])
		for l in localvars:
			self.interference_graph[l] = set([])
			self.move_graph[l] = set([])
		for l in self.registers:
			self.interference_graph[l] = set([])
			self.move_graph[l] = set([])
		self.handle(n.node)
	
	def handleASMStmt(self, n):
		for s in reversed(n.nodes):
			self.handle(s)
	
	def handleASMArithmetic(self, n):
		left = n.getSrc()
		right = n.getDest()
		
		if isinstance(n,ASMMove) and isinstance(right, ASMLoc):
			for v in n.live:
				if left != right:
					self.add_interference(v, right)
			self.add_move(left,right)
			
		elif isinstance(right,ASMLoc):
			if left != right:
				for v in n.live:
					self.add_interference(v,right)
	
	def handleASMCall(self, n):
		for v in n.live:
			if ASMReg('eax') in self.get_vertices():
				self.add_interference(v,ASMReg('eax'))
			if ASMReg('ecx') in self.get_vertices():
				self.add_interference(v,ASMReg('ecx'))
			if ASMReg('edx') in self.get_vertices():
				self.add_interference(v,ASMReg('edx'))
	
	def handleASMPush(self,n):
		pass
	
	def handleASMPop(self,n):
		pass
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
			vertices_str += '''"%r"[color=%s,label="%r.%s"]\n''' % \
							(v, self.get_color(real_color, color[v], num_registers), \
							v, repr(i))
			for u in self.get_interferences(v):
				if (v,u) not in edges:
					edges |= set([(u,v)])
			i += 1
		edges_str = '\n'.join(['"%r" -- "%r"' % (u,v)
							  for (u,v) in edges])
		f = open(filename, 'w')
		stdout = sys.stdout
		sys.stdout = f
		print 'graph {\n%s\n%s\n}\n' % (vertices_str, edges_str)
		sys.stdout = stdout
		f.close()
		
	
	
