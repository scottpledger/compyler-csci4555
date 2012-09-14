#!/usr/bin/python2

import mglobals
from compiler import *
from compiler.ast import *

class ASMNode:
	pass

class ASMCall(ASMNode):
	__init__(self,node):
		self.node = node

class ASMMove(ASMNode):
	__init__(self,src,dest):
		self.src  = src
		self.dest = dest

class ASMReg(ASMNode):
	__init__(self,name):
		self.name = name

class ASMConst(ASMNode):
	__init__(self,value):
		self.value = value

class ASMAdd(ASMNode):
	__init__(self,src,dest):
		self.src  = src
		self.dest = dest
	


def flatnode_to_asm(n, output):
	x86Str = ''
	if isinstance( n, Assign ):
		if isinstance( n.expr, CallFunc ):#call input instruction
			if (n.expr.node.name == 'input'):
				x86Str += '''
	call input
	movl %eax, ''' + str(mglobals.varoff_dict[n.nodes.name]) + '''(%ebp)'''

		elif isinstance( n.expr, UnarySub ):#negl instruction
			if isinstance( n.expr.expr, Name):#negl var
				x86Str = x86Str + '''
	movl ''' + str(mglobals.varoff_dict[n.expr.expr.name]) + '''(%ebp), %eax
	negl %eax
	movl %eax, ''' + str(mglobals.varoff_dict[n.nodes.name]) + '''(%ebp)'''
	
			elif( isinstance( n.expr.expr, Const)):#negl const
				x86Str += '''
	movl $''' + str(n.expr.expr.value) + ''', %eax
	negl %eax
	movl %eax, ''' + str(mglobals.varoff_dict[n.nodes.name]) + '''(%ebp)'''
	
		elif isinstance( n.expr, Name ):#movl var instruction
			x86Str += '''
	movl ''' + str(mglobals.varoff_dict[n.expr.name]) + '''(%ebp), %eax
	movl %eax, ''' + str(mglobals.varoff_dict[n.nodes.name]) + '''(%ebp)'''
	
		elif isinstance( n.expr, Const ):#movl const instruction
			x86Str += '''
	movl $''' + str(n.expr.value) + ''', ''' + str(mglobals.varoff_dict[n.nodes.name]) + '''(%ebp)'''
	
		elif isinstance( n.expr, Add ):#addl instruciton
			
			if isinstance( n.expr.left, Name):
				x86Str += '''
	movl ''' + str(mglobals.varoff_dict[n.expr.left.name]) + '''(%ebp), %eax'''
			elif isinstance( n.expr.left, Const):
				x86Str += '''
	movl $''' + str(n.expr.left.value) + ''', %eax'''
			if isinstance( n.expr.right, Name):
				x86Str += '''
	movl ''' + str(mglobals.varoff_dict[n.expr.right.name]) + '''(%ebp), %ebx'''
			elif isinstance( n.expr.right, Const):
				x86Str += '''
	movl $''' + str(n.expr.right.value) + ''', %ebx'''
			x86Str += '''
	addl %ebx, %eax
	movl %eax, ''' + str(mglobals.varoff_dict[n.nodes.name]) + '''(%ebp)'''
				
	elif isinstance( n, CallFunc ):#print_int_nl instruciton
		if (n.node.name == 'print_int_nl'):
			if isinstance( n.args[0], Name):
				x86Str += '''
	push ''' + str(mglobals.varoff_dict[n.args[0].name]) + '''(%ebp)'''
			elif isinstance( n.args[0], Const):
				x86Str += '''
	push $''' + str(n.args[0].value)
			x86Str += '''
	call print_int_nl
	addl $4, %esp'''
	output.write(x86Str)

def flattened_to_asm(flattened,output):
	# Okay, so first we need to set up where variables will be located relative to the ebp(?).
	offset = + 4
	mglobals.varname_set = set(mglobals.varname_lst)
	for var in mglobals.varname_set:
		mglobals.varoff_dict[var]=-offset
		offset = offset + 4
	# with that now made, we can call flatnode_to_asm to write the actual output.
	output.write('''
.globl main
main:
	pushl %ebp
	movl %esp, %ebp
	subl $'''+str(offset)+''', %esp
''')#preparation

	for line in flattened:
		flatnode_to_asm(line,output)

	output.write('''
	movl $0, %eax 
	leave
	ret
''')#clean up


