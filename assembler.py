#!/usr/bin/python2

import mglobals
from compiler import *
from compiler.ast import *


class ASMNode:
	def __str__( self ):
		return ''

class ASMFile(ASMNode):
	def __init__(self,nodes):
		self.nodes = nodes
	def __str__( self ):
		val = ''
		for n in self.nodes:
			val += str(n) + '\n'
		return val

class ASMGlobl(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return '.globl '+str(self.name)

class ASMFunc(ASMNode):
	def __init__(self,name,nodes):
		self.name  = name
		self.nodes = [
			ASMPush( ASMReg('ebp') ),
			ASMMove( ASMReg('esp'), ASMReg('ebp') )
		] + nodes + [
			ASMNode(),
			ASMMove( ASMConst(0), ASMReg('eax') ),
			ASMLeave(),
			ASMRet()
		]
	def __str__( self ):
		val = str(self.name) + ':\n'
		for n in self.nodes:
			val += '\t'+str(n)+'\n'
		return val

class ASMCall(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'call '+str(self.node)+' '

class ASMLabel(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return self.name

class ASMMove(ASMNode):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'movl '+str(self.left)+', '+str(self.right)+' '

class ASMReg(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return '%'+str(self.name)

class ASMVar(ASMNode):
	def __init__(self,name,reg):
		self.name = name
		self.reg  = reg
	def __str__( self ):
		return str(mglobals.varoff_dict[self.name])+'('+str(self.reg)+')'

class ASMConst(ASMNode):
	def __init__(self,value):
		self.value = value
	def __str__( self ):
		return '$'+str(self.value)

class ASMAdd(ASMNode):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'addl '+str(self.left)+', '+str(self.right)+' '

class ASMSub(ASMNode):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'subl '+str(self.left)+', '+str(self.right)+' '

class ASMNeg(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'negl '+str(self.node)+' '

class ASMPush(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'push '+str(self.node)+' '

class ASMLeave(ASMNode):
	def __str__( self ):
		return 'leave '
		

class ASMRet(ASMNode):
	def __str__( self ):
		return 'ret '

class ASMComment(ASMNode):
	def __init__(self,comment):
		self.comment = comment
	def __str__( self ):
		return '#'+str(self.comment)


def flatnode_to_asm(n, output):
	asm_nodes = [ASMNode(),ASMComment('from '+str(n))]
	x86Str = ''
	if isinstance( n, Assign ):
		if isinstance( n.expr, CallFunc ):#call input instruction
			if (n.expr.node.name == 'input'):
				asm_nodes += [
					ASMCall( ASMLabel('input') ),
					ASMMove( ASMReg('eax'), ASMVar( n.nodes.name, ASMReg('ebp') ) )
				]

		elif isinstance( n.expr, UnarySub ):#negl instruction
			if isinstance( n.expr.expr, Name):#negl var
				asm_nodes += [
					ASMMove( ASMVar( n.expr.expr.name, ASMReg('ebp') ), ASMReg('eax') ),
					ASMNeg( ASMReg('eax') ),
					ASMMove( ASMReg('eax'), ASMVar( n.nodes.name, ASMReg('ebp') ) )
				]
	
			elif( isinstance( n.expr.expr, Const)):#negl const
				asm_nodes += [
					ASMMove( ASMConst( n.expr.expr.value ), ASMReg('eax') ),
					ASMNeg( ASMReg('eax') ),
					ASMMove( ASMReg('eax'), ASMVar( n.nodes.name, ASMReg('ebp') ) )
				]
	
		elif isinstance( n.expr, Name ):#movl var instruction
			asm_nodes += [
				ASMMove( ASMVar( n.expr.name, ASMReg('ebp') ), ASMReg('eax') ),
				ASMMove( ASMReg('eax'), ASMVar( n.nodes.name, ASMReg('ebp') ) )
			]
	
		elif isinstance( n.expr, Const ):#movl const instruction
			asm_nodes += [
				ASMMove( ASMConst(n.expr.value), ASMVar( n.nodes.name, ASMReg('ebp') ) )
			]
	
		elif isinstance( n.expr, Add ):#addl instruciton
			lnode = ASMNode()
			rnode = ASMNode()
			if isinstance( n.expr.left, Name):
				lnode = ASMMove( ASMVar( n.expr.left.name, ASMReg('ebp') ), ASMReg('eax') )
	
			elif isinstance( n.expr.left, Const):
				lnode = ASMMove( ASMConst( n.expr.left.value ), ASMReg('eax') )
				
			if isinstance( n.expr.right, Name):
				rnode = ASMMove( ASMVar( n.expr.right.name, ASMReg('ebp') ), ASMReg('ebx') )
				
			elif isinstance( n.expr.right, Const):
				rnode = ASMMove( ASMConst( n.expr.right.value ), ASMReg('ebx') )
			
			asm_nodes += [
				lnode,
				rnode,
				ASMAdd( ASMReg('ebx'), ASMReg('eax') ),
				ASMMove( ASMReg('eax'), ASMVar( n.nodes.name, ASMReg('ebp') ) )
			]
				
	elif isinstance( n, CallFunc ):#print_int_nl instruciton
		if (n.node.name == 'print_int_nl'):
			push_n = ASMConst(0)
			if isinstance( n.args[0], Name):
				push_n = ASMVar( n.args[0].name, ASMReg('ebp') )
				
			elif isinstance( n.args[0], Const):
				push_n = ASMConst( n.args[0].value )

			asm_nodes += [
				ASMPush( push_n ),
				ASMCall( ASMLabel('print_int_nl') ),
				ASMAdd( ASMConst(4), ASMReg('esp') )
			]
	
	return asm_nodes

def flattened_to_asm(flattened,output):
	# Okay, so first we need to set up where variables will be located relative to the ebp.
	offset = + 4
	mglobals.varname_set = set(mglobals.varname_lst)
	for var in mglobals.varname_set:
		mglobals.varoff_dict[var]=-offset
		offset = offset + 4
	# with that now made, we can call flatnode_to_asm to write the actual output.
	
	func_nodes = [
		ASMSub( ASMConst(str(offset)), ASMReg('esp') )
	]
	
	for line in flattened:
		func_nodes += flatnode_to_asm(line,output)
	
	asm_file = ASMFile([
		ASMGlobl( ASMLabel('main') ),
		ASMFunc ( ASMLabel('main') , func_nodes )
	])
	
	output.write(str(asm_file))


