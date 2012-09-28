#!/usr/bin/python2.7
import mglobals
from compiler import *
from compiler.ast import *
from flattener import TempName
from asmnodes import *

class InterferenceGraph:
	def __init__(self):
		self.dict = {}
		self.reg_assign = {}
		self.avail_regs = set([ASMReg('eax'),ASMReg('ebx'),ASMReg('ecx'),ASMReg('edx'),ASMReg('edi'),ASMReg('esi')])
		self.stack_size = -4
	
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
		pass
	
	

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
		
		for x in range(0,max(len(self.live_variables),len(out_list))):
			left = None
			right = None
			if x<len(asm_list):
				left = asm_list[x]
			if x<len(self.live_variables):
				right = self.live_variables[x]
			print "%r => %r"%(right,left)
		
		print "Graph Edges: "
		for key in self.int_graph.dict.iterkeys():
			print "%r => %r"%(key,self.int_graph.dict[key])
		
		print "Graph assigns:"
		for key in self.int_graph.reg_assign:
			print "%r => %r"%(key,self.int_graph.reg_assign[key])
		
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
			
			for n in W_v | R_v:
				self.int_graph.add_node(n)
			
		return out_list
		
	def build_interference_graph(self, asm_list):
		out_list = asm_list
		stack = list(out_list)
		while len(stack)>0:
			instr = stack.pop()
			L_before = self.live_variables[len(stack)]
			L_after = self.live_variables[len(stack)+1]
			
			if isinstance(instr, ASMMove) and instr.right in L_after:
				self.int_graph.add_edges(instr.right, (L_after-set([instr.left]))-set([instr.right]))
			elif isinstance(instr, ASMAdd) and instr.right in L_after:
				self.int_graph.add_edges(instr.right, L_after-instr.right)
			elif isinstance(instr, ASMCall):
				call_save_regs = set([ASMReg('eax'),ASMReg('ecx'),ASMReg('edx')])
				for x in L_after:
					self.int_graph.add_edges(x,call_save_regs)
				
				

		
	
