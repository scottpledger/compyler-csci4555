#!/usr/bin/python2

import mglobals
from compiler import *
from compiler.ast import *
import flattener
from flattener import TempName
from flattener import VarName
from rallocator import RegisterAllocator

from asmnodes import *


def flatnode_to_asm(n):
	#asm_nodes = [ASMNode(),ASMComment('from '+str(n))]
	asm_nodes = []
	x86Str = ''
	if isinstance( n, Assign ):
		if isinstance( n.expr, CallFunc ):#call input instruction
			if (n.expr.node.name == 'input'):
				asm_nodes += [
					ASMCall( ASMLabel('input') ),
					ASMMove( ASMReg('eax'), ASMVar( n.nodes ) )
				]

		elif isinstance( n.expr, UnarySub ):#negl instruction
			
			if isinstance( n.expr.expr, VarName):# and n.expr.expr.vtype=='user':#negl var
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
	
	offset = + 4
	
	
	func_nodes = [
		#ASMSub( ASMConst(str(offset)), ASMReg('esp') )
	]
	
	flattened.append(Node())
	
	
	i=0
	while i < len(flattened)-1:
		#Let's do a bit of clean up here, before converting it to asm...
		line = flattened[i]
		#n_line = flattened[i+1]
		#if isinstance(line, Assign) and isinstance(n_line,Assign) and n_line.expr == line.nodes:
		#	n_line.expr = line.expr
		#	line = n_line
		#	i+=1
		func_nodes += flatnode_to_asm(line)
		i+=1
	
	ralloc = RegisterAllocator()
	func_nodes = ralloc.allocate_registers(func_nodes)
	new_func_nodes = []
	for n in func_nodes:
		if isinstance(n,ASMMove):
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
	
			if not str(lloc)==str(rloc):
				new_func_nodes.append(n)
		else:
			new_func_nodes.append(n)
	func_nodes = new_func_nodes
	
	
	func_nodes = [
		ASMSub( ASMConst(str(4*(len(ralloc.int_graph.avail_stacks)))), ASMReg('esp') )
	] + func_nodes
	
	asm_file = ASMFile([
		ASMGlobl( ASMLabel('main') ),
		ASMFunc ( ASMLabel('main') , func_nodes )
	])
	
	return asm_file
	
	#output.write(str(asm_file))


