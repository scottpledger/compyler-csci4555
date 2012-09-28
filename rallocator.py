#!/usr/bin/python2.7
import mglobals
from compiler import *
from compiler.ast import *
from flattener import TempName
from asmnodes import *
import heapq

class PriorityQueue:
	def  __init__(self):  
		self.heap = []

	def push(self, item, priority):
		pair = (priority,item)
		heapq.heappush(self.heap,pair)

	def pop_min(self):
		(priority,item) = heapq.heappop(self.heap)
		return item
	
	def pop_max(self):
		vals = heapq.nlargest(1,self.heap)
		(priority,item) = vals[0]
		self.heap.remove((priority,item))
		return item

	def is_empty(self):
		return len(self.heap) == 0


class InterferenceGraph:
	def __init__(self):
		self.dict = {}
		self.reg_assign = {}
		self.avail_regs = set([ASMReg('eax'),ASMReg('ebx'),ASMReg('ecx'),ASMReg('edx'),ASMReg('edi'),ASMReg('esi')])
		self.avail_stacks = set([])
	
	def add_node(self, node):
		if node not in self.dict:
			self.dict[node] = set([])
		
	def add_edge(self, node1, node2):
		if not node1 == node2:
			if node1 not in self.dict:
				self.dict[node1] = set([])
			if node2 not in self.dict:
				self.dict[node2] = set([])
			self.dict[node1].add(node2)
			self.dict[node2].add(node1)
			
			if isinstance(node1, ASMReg):
				self.reg_assign[node1] = node1
			else:
				self.reg_assign[node1] = None
			
			if isinstance(node2, ASMReg):
				self.reg_assign[node2] = node2
			else:
				self.reg_assign[node2] = None
	
	def add_edges(self, node1, nodeset):
		for node2 in nodeset:
			self.add_edge(node1,node2)
	
	def get_saturation(self, node):
		if self.reg_assign[node] == None:
			saturation = 0
			for child in self.dict[node]:
				if not self.reg_assign[child] == None:
					saturation += 1
			return saturation
		else:
			return 9999999999999999999999999999999999
	
	def assign_locations(self):
		queue = PriorityQueue()
		for node in self.dict:
			
			queue.push(node,self.get_saturation(node))
		
		while not queue.is_empty():
			node = queue.pop_max()
			m_regs = set(self.avail_regs)
			m_stacks= set(self.avail_stacks)
			for child in self.dict[node]:
				#print "checking child "+repr(child)+" against "+repr(self.reg_assign)
				if child in self.reg_assign and not self.reg_assign[child] == None:
					color = self.reg_assign[child]
					if isinstance(color,ASMReg):
						m_regs = m_regs - set([color])
					else:
						m_stacks = m_stacks - set([color])
			
			if len(m_regs)>0:
				self.reg_assign[node] = m_regs.pop()
				self.changed = True
			elif len(m_stacks)>0:
				self.reg_assign[node] = m_stacks.pop()
				self.changed = True
			else:
				new_stack = ASMStack(ASMReg('ebp'),-4*(1+len(self.avail_stacks)))
				self.avail_stacks.add(new_stack)
				self.reg_assign[node] = new_stack
				self.changed = True
			
	
	

class RegisterAllocator:
	def __init__(self):
		self.live_variables = []
		self.changed = True
		self.int_graph = InterferenceGraph()
		
	def allocate_registers(self,asm_list):
		out_list = asm_list
		n=len(out_list)
		self.live_variables = list([set([]) for i in range(0,n+1)])
		while self.changed:
			self.changed=False
			out_list = self.analyse_liveness(out_list)
			self.build_interference_graph(out_list)
			self.int_graph.assign_locations()
			out_list = self.verify_assignments(out_list)
			#self.changed=False
			
		
		#print "Live variable sets:"
		#for x in range(0,max(len(self.live_variables),len(out_list))):
		#	left = None
		#	right = None
		#	if x<len(asm_list):
		#		left = asm_list[x]
		#	if x<len(self.live_variables):
		#		right = self.live_variables[x]
		#	print "%r => %r"%(right,left)
		#
		#print "Graph Edges: "
		#for key in self.int_graph.dict.iterkeys():
		#	print "%r => %r"%(key,self.int_graph.dict[key])
		
		#print "Graph assigns:"
		#for key in self.int_graph.reg_assign:
		#	print "%r => %r"%(key,self.int_graph.reg_assign[key])
		
		for n in out_list:
			if isinstance(n,ASMAdd) or isinstance(n,ASMMove):
				if isinstance(n.left,ASMVar):
					n.left.loc = self.int_graph.reg_assign[n.left.name]
				if isinstance(n.right,ASMVar):
					n.right.loc = self.int_graph.reg_assign[n.right.name]
			elif isinstance(n,ASMNeg) or isinstance(n,ASMPush):
				if isinstance(n.node,ASMVar):
					n.node.loc = self.int_graph.reg_assign[n.node.name]
		
		return out_list
	
	def analyse_liveness(self,asm_list):
		out_list = asm_list
		stack = list(out_list)
		while len(stack)>0:
			instr = stack.pop()
			
			W_v = set([]) # Variables written to
			R_v = set([]) # Variables read to
			
			# Variables read
			if isinstance(instr, ASMAdd):
				if isinstance(instr.left, ASMVar):
					R_v.add(instr.left.name)
				if isinstance(instr.right,ASMVar):
					R_v.add(instr.right.name)
					W_v.add(instr.right.name)
			
			elif isinstance(instr, ASMMove):
				if isinstance(instr.left, ASMVar):
					R_v.add(instr.left.name)
				if isinstance(instr.right,ASMVar):
					W_v.add(instr.right.name)
					
			elif isinstance(instr, ASMNeg):
				if isinstance(instr.node, ASMVar):
					W_v.add(instr.node.name)
					R_v.add(instr.node.name)
			
			elif isinstance(instr,ASMPush):
				if isinstance(instr.node, ASMVar):
					R_v.add(instr.node.name)
			

			L_before = self.live_variables[len(stack)]
			L_after = self.live_variables[len(stack)+1]
			L_before = (L_after - W_v) | R_v
			if not self.live_variables[len(stack)] == L_before:
				self.changed=True
				self.live_variables[len(stack)] = L_before
			
		return out_list
		
	def build_interference_graph(self, asm_list):
		out_list = asm_list
		stack = list(out_list)
		
		for i in range(0,len(stack)-1):
			instr = stack[i]
			L_before = self.live_variables[i]
			L_after = self.live_variables[i+1]
			#print "Checking: "+repr(instr)+ " with "+repr(L_after)
			
			#print "right: "+repr(instr.right.name)+" in L_after? "+str(instr.right.name in L_after)
			if isinstance(instr, ASMMove) and isinstance(instr.right, ASMVar) and (instr.right.name in L_after):
				nset = L_after - set([instr.right.name])
				if isinstance(instr.left, ASMVar):
					nset = L_after - set([instr.left.name,instr.right.name])
				self.int_graph.add_edges(instr.right.name, nset )
			elif isinstance(instr, ASMAdd) and isinstance(instr.right, ASMVar) and instr.right.name in L_after:
				self.int_graph.add_edges(instr.right.name, L_after-set([instr.right.name]))
			elif isinstance(instr, ASMCall):
				call_save_regs = set([ASMReg('eax'),ASMReg('ecx'),ASMReg('edx')])
				for x in L_after:
					self.int_graph.add_edges(x,call_save_regs)

	def verify_assignments(self, asm_list):
		out_list = []
		for n in asm_list:
			if (
				(isinstance(n, ASMAdd) or isinstance(n, ASMMove)) and 
				isinstance(n.left, ASMVar) and isinstance(n.right, ASMVar) and 
				isinstance(self.int_graph.reg_assign[n.left.name],ASMStack) and 
				isinstance(self.int_graph.reg_assign[n.right.name],ASMStack)
				):
					temp_var = flattener.gen_temp('reg_temp')
					out_list.append(ASMMove(n.left,ASMVar(temp_var)))
					if isinstance(n,ASMAdd):
						out_list.append(ASMAdd(ASMVar(temp_var),n.right))
					else:
						out_list.append(ASMMove(ASMVar(temp_var),n.right))
					self.changed=True
			else:
				out_list.append(n)
				
					
		return out_list
				
				

		
	
