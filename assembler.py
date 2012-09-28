#!/usr/bin/python2

import mglobals
from compiler import *
from compiler.ast import *
from flattener import TempName
from flattener import VarName
from rallocator import RegisterAllocator

from asmnodes import *


def flatnode_to_asm(n):
	asm_nodes = [ASMNode(),ASMComment('from '+str(n))]
	#asm_nodes = []
	x86Str = ''
	if isinstance( n, Assign ):
		if isinstance( n.expr, CallFunc ):#call input instruction
			if (n.expr.node.name == 'input'):
				asm_nodes += [
					ASMCall( ASMLabel('input') ),
					ASMMove( ASMReg('eax'), ASMVar( n.nodes ) )
				]

		elif isinstance( n.expr, UnarySub ):#negl instruction
			
			if isinstance( n.expr.expr, VarName) and n.expr.expr.vtype=='user':#negl var
				if n.expr.expr == n.nodes:
					asm_nodes += [
						ASMNeg( ASMVar(n.expr.expr) )
					]
				else:
					asm_nodes += [
						ASMMove( ASMVar( n.expr.expr ), ASMVar( n.nodes ) ),
						ASMNeg( ASMVar( n.nodes ) )
					]
	
			elif( isinstance( n.expr.expr, Const)):#negl const
				asm_nodes += [
					ASMMove( ASMConst( n.expr.expr.value ), ASMVar( n.nodes ) ),
					ASMNeg( ASMVar( n.nodes ) )
				]
	
		elif isinstance( n.expr, VarName ):#movl var instruction
			asm_nodes += [
				ASMMove( ASMVar( n.expr ), ASMVar( n.nodes ) )
			]
	
		elif isinstance( n.expr, Const ):#movl const instruction
			asm_nodes += [
				ASMMove( ASMConst(n.expr.value), ASMVar( n.nodes ) )
			]
	
		elif isinstance( n.expr, Add ):#addl instruciton
			lnode = None
			rnode = None
			fnode = ASMVar(n.nodes)
			
			if isinstance( n.expr.left, VarName):
				lnode = ASMVar( n.expr.left )
	
			elif isinstance( n.expr.left, Const):
				lnode = ASMConst( n.expr.left.value )
				
			if isinstance( n.expr.right, VarName):
				rnode = ASMVar( n.expr.right )
				
			elif isinstance( n.expr.right, Const):
				rnode = ASMConst( n.expr.right.value )
			
			if isinstance( lnode, ASMConst) and isinstance( rnode, ASMConst):
				asm_nodes += [
					ASMMove( lnode, fnode ),
					ASMAdd( rnode , fnode )
				]
			elif n.expr.left == n.nodes:
				asm_nodes += [
					ASMAdd( rnode, fnode )
				]
			elif n.expr.right == n.nodes:
				asm_nodes += [
					ASMAdd( lnode, fnode )
				]
			elif isinstance(lnode, ASMConst):
				asm_nodes += [
					ASMMove( rnode, fnode ),
					ASMAdd ( lnode, fnode )
				]
			elif isinstance(rnode, ASMConst):
				asm_nodes += [
					ASMMove( lnode, fnode ),
					ASMAdd ( rnode, fnode )
				]
			else:
				asm_nodes += [
					ASMMove( lnode, fnode ),
					ASMAdd ( rnode, fnode )
				]

				
	elif isinstance( n, CallFunc ):#print_int_nl instruciton
		if (n.node.name == 'print_int_nl'):
			push_n = ASMConst(0)
			if isinstance( n.args[0], VarName):
				push_n = ASMVar( n.args[0] )
				
			elif isinstance( n.args[0], Const):
				push_n = ASMConst( n.args[0].value )

			asm_nodes += [
				ASMPush( push_n ),
				ASMCall( ASMLabel('print_int_nl') ),
				ASMAdd( ASMConst(4), ASMReg('esp') )
			]
	
	return asm_nodes

#def flattened_to_asm(flattened,output):
def flattened_to_asm(flattened):
	# Okay, so first we need to set up where variables will be located relative to the ebp.
	offset = + 4
	#print mglobals.varname_lst
	#mglobals.varname_set = set(mglobals.varname_lst)
	#print mglobals.varname_set
	#for var in mglobals.varname_set:
	#s	if isinstance(var, TempName):
	#		mglobals.tvaroff_dict[var.name]=-offset
	#	else:
	#		mglobals.varoff_dict[var.name]=-offset
	#	offset = offset + 4
	# with that now made, we can call flatnode_to_asm to write the actual output.
	ralloc = RegisterAllocator()
	func_nodes = [
		#ASMSub( ASMConst(str(offset)), ASMReg('esp') )
	]
	
	for line in flattened:
		func_nodes += flatnode_to_asm(line)
	
	ralloc.analyse_liveness(func_nodes)
	
	asm_file = ASMFile([
		ASMGlobl( ASMLabel('main') ),
		ASMFunc ( ASMLabel('main') , func_nodes )
	])
	
	return asm_file
	
	#output.write(str(asm_file))


