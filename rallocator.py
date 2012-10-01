#!/usr/bin/python2.7
import mglobals
from compiler import *
from compiler.ast import *
from flattener import TempName
from flattener import VarName
from asmnodes import *
import heapq
import flattener

class PriorityQueue:
	def  __init__(self,pfunc):  
		self.heap = []
		self.pfunc = pfunc

	def push(self, item):
		pair = (self.pfunc(item),item)
		heapq.heappush(self.heap,pair)

	def pop_min(self):
		(priority,item) = heapq.heappop(self.heap)
		return item
	
	def pop_max(self):
		vals = heapq.nlargest(1,self.heap)
		(priority,item) = vals[0]
		self.heap.remove((priority,item))
		return item
	
	def update(self):
		oldheap = self.heap
		self.heap = []
		for p,n in oldheap:
			self.push(n)

	def is_empty(self):
		return len(self.heap) == 0


class InterferenceGraph:
	def __init__(self):
		self.dict = {}
		self.reg_assign = {}
		self.avail_regs = set([ASMReg('eax'),ASMReg('ebx'),ASMReg('ecx'),ASMReg('edx'),ASMReg('edi'),ASMReg('esi')])
		self.avail_stacks = set([])
		self.changed = True
	
	def add_node(self, node):
		if node not in self.dict:
			self.dict[node] = set([])
		if node not in self.reg_assign:
			self.reg_assign[node] = None
		
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
		if isinstance(node, VarName) and node.vtype =='reg_temp':
			return 9999999999999999999999999999999999
		elif self.reg_assign[node]:
			saturation = 0
			for child in self.dict[node]:
				if not self.reg_assign[child] == None:
					saturation += 1
			return saturation
		else:
			return 99999999999999999
	
	def assign_locations(self):
		self.reg_assign = {}
		queue = PriorityQueue(self.get_saturation)
		for node in self.dict:
			self.reg_assign[node] = None
			queue.push(node)
		
		while not queue.is_empty():
			node = queue.pop_max()
			m_regs = set(self.avail_regs)
			m_stacks= set(self.avail_stacks)
			for child in self.dict[node]:
				if child in self.reg_assign and not self.reg_assign[child] == None:
					color = self.reg_assign[child]
					if isinstance(color,ASMReg):
						m_regs = m_regs - set([color])
					else:
						m_stacks = m_stacks - set([color])
			newval = None
			if len(m_regs)>0:
				newval = m_regs.pop()
				
			elif len(m_stacks)>0:
				newval = m_stacks.pop()
				
			else:
				newval = ASMStack(ASMReg('ebp'),-4*(1+len(self.avail_stacks)))
				self.avail_stacks.add(newval)
				
			if not self.reg_assign[node] == newval:
				self.reg_assign[node] = newval
				self.changed = True
			# Now we need to update our priority queue!
			queue.update()
			
	
	

class RegisterAllocator:
	def __init__(self):
		self.live_variables = []
		self.changed = True
		self.int_graph = InterferenceGraph()
		
	def allocate_registers(self,asm_list):
		out_list = list(asm_list)
		n=len(out_list)
		self.live_variables = list([set([]) for i in range(0,n+1)])
		prev_list = list()
		allocated = False
		self.changed = True
		passnum = 0
		while self.changed:
			
			self.changed = False
			prev_list = list(out_list)
		
			#print "Iteration %s" % passnum
			
			n=len(out_list)
			self.live_variables = self.live_variables + list([set([]) for i in range(len(self.live_variables),n+1)])
			
			out_list = self.analyse_liveness(out_list)
			# For debugging, let's write out the live analysis results...
			ofile = open('tmp/rallocator/pass'+str(passnum)+'.live_vars','w')
			for j in range(0,len(self.live_variables)):
				ofile.write("%r\n"%self.live_variables[j])
				if j < len(out_list):
					ofile.write("\t%r\n"%out_list[j])
			
			self.build_interference_graph(out_list)
			# For debugging, let's write out the interference graph...
			ofile = open('tmp/rallocator/pass'+str(passnum)+'.int_graph','w')
			for i in self.int_graph.dict.iterkeys():
				ofile.write( "%r\n"%i )
				for j in self.int_graph.dict[i]:
					ofile.write( "\t=> %r\n"%(j) )
			
			
			self.int_graph.assign_locations()
			out_list = self.verify_assignments(out_list)
			
			new_list = []
			allocated = True
			for n in out_list:
				append = True
				if isinstance(n,ASMAdd) or isinstance(n,ASMMove):
					if isinstance(n.left,ASMVar):
						try:
							n.left.loc = self.int_graph.reg_assign[n.left.name]
						except KeyError:
							allocated = False
					if isinstance(n.right,ASMVar):
						try:
							n.right.loc = self.int_graph.reg_assign[n.right.name]
						except KeyError:
							allocated = False
					
					
				elif isinstance(n,ASMNeg) or isinstance(n,ASMPush):
					if isinstance(n.node,ASMVar):
						try:
							n.node.loc = self.int_graph.reg_assign[n.node.name]
						except KeyError:
							allocated = False
			
				if append:
					new_list.append(n)
			out_list = list(new_list)
			
			
			if False:
				new_list = []
				ofile = open('tmp/rallocator/pass'+str(passnum)+'.rem_dupes','w')
				for n in out_list:
					append = True
					if isinstance(n,ASMMove):
						ofile.write("Checking: %r\n"%n)
						lloc = ""
						rloc = ""
						if isinstance(n.left,ASMVar):
							lloc = n.left.loc
						elif isinstance(n.left,ASMReg):
							lloc = n.left
					
						if isinstance(n.right,ASMVar):
							rloc = n.right.loc
						elif isinstance(n.right,ASMReg):
							rloc = n.right
					
						if str(lloc)==str(rloc):
							append = False
							self.changed = True
						ofile.write( "to see if %s == %s , which is %r\n"%(lloc,rloc,not append) )
					
					if append:
						new_list.append(n)
				
				out_list = list(new_list)
					
			
			ofile = open('tmp/rallocator/pass'+str(passnum)+'.asm_list','w')
			passnum += 1
			for n in out_list:
				ofile.write("%r\n"%n)
			
			
		
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
				
			for n in R_v | W_v:
				self.int_graph.add_node(n)
			
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
		#return asm_list
		out_list = []
		for n in asm_list:
			if (
				( isinstance(n, ASMAdd) or isinstance(n, ASMMove) ) and 
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
			elif isinstance(n,ASMMove) and False:
				lloc = ""
				rloc = ""
				if isinstance(n.left,ASMVar):
					lloc = n.left.loc
				elif isinstance(n.left,ASMReg):
					lloc = n.left
			
				if isinstance(n.right,ASMVar):
					rloc = n.right.loc
				elif isinstance(n.right,ASMReg):
					rloc = n.right
			
				if str(lloc)==str(rloc):
					self.changed = True
				else:
					out_list.append(n)
			

			else:
				#print "Valid node: "+repr(n)
				out_list.append(n)
				
					
		return out_list
				
				

		
	
