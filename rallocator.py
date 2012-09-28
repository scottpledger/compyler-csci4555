#!/usr/bin/python2.7
import mglobals
from compiler import *
from compiler.ast import *
from flattener import TempName
from asmnodes import *

class RegisterAllocator:
	def __init__(self):
		self.live_variables = []
		self.changed = True
		
	def allocate_registers(self,asm_list):
		out_list = list(asm_list)
		
		while self.changed:
			self.changed=False
			n=len(asm_list)
			self.live_variables = list([set([]) for i in range(0,n+1)])
			out_list = self.analyse_liveness(out_list)
		
		for x in range(0,max(len(self.live_variables),len(out_list))):
			left = None
			right = None
			if x<len(asm_list):
				left = asm_list[x]
			if x<len(self.live_variables):
				right = self.live_variables[x]
			print "%r => %r"%(right,left)
		
		return out_list
	
	def analyse_liveness(self,asm_list):
		
		out_list = asm_list
		stack = list(out_list)
		if len(stack) > len(self.live_variables):
			n=len(asm_list)
			self.live_variables = list([set([]) for i in range(0,n+1)])

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
	
