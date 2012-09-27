#!/usr/bin/python2

import mglobals
from compiler import *
from compiler.ast import *
from flattener import TempName

class ASMNode:
	def __str__( self ):
		return ''
	def __repr__( self ):
		return "ASMNode()"

class ASMFile(ASMNode):
	def __init__(self,nodes):
		self.nodes = nodes
	def __str__( self ):
		val = ''
		for n in self.nodes:
			n_str = str(n)
			val += n_str + '\n'			
		return val
	def __repr__( self ):
		return "ASMFile(%r)" % self.nodes

class ASMGlobl(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return '.globl '+str(self.name)
	def __repr__( self ):
		return "ASMGlobl(%r)" % self.name

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
	def __repr__( self ):
		return "ASMFunc(%r,%r)" % (self.name, self.nodes)

class ASMCall(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'call '+str(self.node)+' '
	def __repr__( self ):
		return "ASMCall(%r)" % self.node

class ASMLabel(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return self.name
	def __repr__( self ):
		return "ASMLabel(%r)" % self.name

class ASMMove(ASMNode):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'movl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMMove(%r,%r)" % (self.left, self.right)

class ASMReg(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return '%'+str(self.name)
	def __repr__( self ):
		return "ASMReg(%r)" % self.name

class ASMVar(ASMNode):
	def __init__(self,name,reg):
		self.name = name
		self.reg  = reg
	def __repr__( self ):
		return "ASMVar(%r,%r)"% (self.name, self.reg )
	def __str__( self ):
		if isinstance(self.name,TempName):
			return str(mglobals.tvaroff_dict[self.name.name])+'('+str(self.reg)+')'
		elif isinstance(self.name,Name):
			return str(mglobals.varoff_dict[self.name.name])+'('+str(self.reg)+')'
		else:
			print "ERROR!!! Could not convert ASMVar(%r,%r) to a string!" % (self.name, self.reg)
			return ''

class ASMConst(ASMNode):
	def __init__(self,value):
		self.value = value
	def __str__( self ):
		return '$'+str(self.value)
	def __repr__( self ):
		return "ASMConst(%r)" % self.value

class ASMAdd(ASMNode):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'addl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMAdd(%r,%r)" % (self.left, self.right)

class ASMSub(ASMNode):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'subl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMSub(%r,%r)" % (self.left, self.right)

class ASMNeg(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'negl '+str(self.node)+' '
	def __repr__( self ):
		return "ASMNeg(%r)" % self.node

class ASMPush(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'push '+str(self.node)+' '
	def __repr__( self ):
		return "ASMPush(%r)" % self.node

class ASMLeave(ASMNode):
	def __str__( self ):
		return 'leave '
	def __repr__( self ):
		return 'ASMLeave()'
		

class ASMRet(ASMNode):
	def __str__( self ):
		return 'ret '
	def __repr__( self ):
		return 'ASMRet()'

class ASMComment(ASMNode):
	def __init__(self,comment):
		self.comment = comment
	def __str__( self ):
		return '#'+str(self.comment)
	def __repr__( self ):
		return "ASMComment(%r)" % self.comment


def flatnode_to_asm(n, output):
	asm_nodes = [ASMNode(),ASMComment('from '+str(n))]
	x86Str = ''
	if isinstance( n, Assign ):
		if isinstance( n.expr, CallFunc ):#call input instruction
			if (n.expr.node.name == 'input'):
				asm_nodes += [
					ASMCall( ASMLabel('input') ),
					ASMMove( ASMReg('eax'), ASMVar( n.nodes, ASMReg('ebp') ) )
				]

		elif isinstance( n.expr, UnarySub ):#negl instruction
			if isinstance( n.expr.expr, Name):#negl var
				asm_nodes += [
					ASMMove( ASMVar( n.expr.expr, ASMReg('ebp') ), ASMReg('eax') ),
					ASMNeg( ASMReg('eax') ),
					ASMMove( ASMReg('eax'), ASMVar( n.nodes, ASMReg('ebp') ) )
				]
	
			elif( isinstance( n.expr.expr, Const)):#negl const
				asm_nodes += [
					ASMMove( ASMConst( n.expr.expr.value ), ASMReg('eax') ),
					ASMNeg( ASMReg('eax') ),
					ASMMove( ASMReg('eax'), ASMVar( n.nodes, ASMReg('ebp') ) )
				]
	
		elif isinstance( n.expr, Name ):#movl var instruction
			asm_nodes += [
				ASMMove( ASMVar( n.expr, ASMReg('ebp') ), ASMReg('eax') ),
				ASMMove( ASMReg('eax'), ASMVar( n.nodes, ASMReg('ebp') ) )
			]
		
		elif isinstance( n.expr, TempName ):
			asm_nodes += [
				ASMMove( ASMVar( n.expr, ASMReg('ebp') ), ASMReg('eax') ),
				ASMMove( ASMReg('eax'), ASMVar( n.nodes, ASMReg('ebp') ) )
			]
	
		elif isinstance( n.expr, Const ):#movl const instruction
			asm_nodes += [
				ASMMove( ASMConst(n.expr.value), ASMVar( n.nodes, ASMReg('ebp') ) )
			]
	
		elif isinstance( n.expr, Add ):#addl instruciton
			lnode = ASMNode()
			rnode = ASMNode()
			if isinstance( n.expr.left, Name) or isinstance( n.expr.left, TempName):
				lnode = ASMMove( ASMVar( n.expr.left, ASMReg('ebp') ), ASMReg('eax') )
	
			elif isinstance( n.expr.left, Const):
				lnode = ASMMove( ASMConst( n.expr.left.value ), ASMReg('eax') )
				
			if isinstance( n.expr.right, Name) or isinstance( n.expr.right, TempName):
				rnode = ASMMove( ASMVar( n.expr.right, ASMReg('ebp') ), ASMReg('ebx') )
				
			elif isinstance( n.expr.right, Const):
				rnode = ASMMove( ASMConst( n.expr.right.value ), ASMReg('ebx') )
			
			asm_nodes += [
				lnode,
				rnode,
				ASMAdd( ASMReg('ebx'), ASMReg('eax') ),
				ASMMove( ASMReg('eax'), ASMVar( n.nodes, ASMReg('ebp') ) )
			]
				
	elif isinstance( n, CallFunc ):#print_int_nl instruciton
		if (n.node.name == 'print_int_nl'):
			push_n = ASMConst(0)
			if isinstance( n.args[0], Name):
				push_n = ASMVar( n.args[0], ASMReg('ebp') )
				
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
	#print mglobals.varname_lst
	mglobals.varname_set = set(mglobals.varname_lst)
	#print mglobals.varname_set
	for var in mglobals.varname_set:
		if isinstance(var, TempName):
			mglobals.tvaroff_dict[var.name]=-offset
		else:
			mglobals.varoff_dict[var.name]=-offset
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
	
	#print asm_file.__repr__()
	
	output.write(str(asm_file))


