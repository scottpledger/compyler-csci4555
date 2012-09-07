#!/usr/bin/python2.7

import os
import os.path
import sys
import argparse
import compiler
import compiler.ast
from compiler.ast import *

temp_var_c = 0
varname_lst = []
varoff_dict = dict()

def gen_temp():
	global temp_var_c
	global varname_lst
	tmp = 't'+str(temp_var_c)
	temp_var_c = temp_var_c + 1
	varname_lst = varname_lst + [tmp]
	return tmp

def flatten(n):
	global varname_lst
	if isinstance(n,Module):
		return flatten(n.node)
	elif isinstance(n,Stmt):
		stmts = []
		for m in n.nodes:
			stmts = stmts + flatten(m)[1]
		return stmts
	elif isinstance(n,Discard):
		#This feels really hacky...
		return flatten(n.expr)
	elif isinstance( n, Assign):
		expr_flat = flatten(n.expr)
		varname_lst = varname_lst + [n.nodes[0].name]
		return ( Name(n.nodes[0].name) , expr_flat[1] + [Assign(n.nodes[0], expr_flat[0])])
	elif isinstance( n, Add ):
		( l, ss1 ) = flatten( n.left  )
		( r, ss2 ) = flatten( n.right )
		t = gen_temp()
		ss3 = [ Assign(AssName(t,'OP_ASSIGN'), Add((l,r))) ]
		return ( Name( t ) , ss1 + ss2 + ss3 )
	elif isinstance( n, Const ):
		return ( n, [] )
	elif isinstance( n, Name ):
		varname_lst = varname_lst + [n.name]
		return ( n, [] )
	elif isinstance( n, CallFunc ):
		t = gen_temp()
		return ( Name( t ), [Assign(AssName(t,'OP_ASSIGN'), n) ] )
	elif isinstance( n, UnarySub ):
		t = gen_temp()
		expr_flat = flatten(n.expr)
		return ( Name(t) , expr_flat[1] + [Assign(AssName(t, 'OP_ASSIGN'), UnarySub( expr_flat[0]))])
	elif isinstance( n, Printnl ):
		nodes_flat = flatten(n.nodes[0])
		return ( None , nodes_flat[1]+[CallFunc(Name('print_int_nl'),[nodes_flat[0]])])

def flatnode_to_asm(n, output):
	global varoff_dict
	x86Str = ''
	if isinstance( n, Assign ):
		if isinstance( n.expr, CallFunc ):#call input instruction
			if n.expr.node.name == 'input':
				x86Str = '''
	call input
	movl %eax, ''' + str(varoff_dict[n.nodes.name]) +'''(%ebp)'''

		elif isinstance( n.expr, UnarySub ):#negl instruction
			x86Str = '''
	movl ''' + str(varoff_dict[n.expr.expr.name]) + '''(%ebp), %eax
	negl %eax
	movl %eax, ''' + str(varoff_dict[n.nodes.name]) +'''(%ebp)'''
		elif isinstance( n.expr, Name ):#movl instruction
			x86Str = '''
	movl ''' + str(varoff_dict[n.expr.name]) + '''(%ebp), ''' + str(varoff_dict[n.nodes.name]) + '''(%ebp)'''
		elif isinstance( n.expr, Add ):#addl instruciton
			x86Str = '''
	movl '''
			if isinstance( n.expr.left, Name):
				x86Str = x86Str + str(varoff_dict[n.expr.left.name]) + '''(%ebp)'''
			elif isinstance( n.expr.left, Const):
				x86Str = x86Str + '''$''' +str(n.expr.left.value) + ''', %eax
	addl '''
			if isinstance( n.expr.right, Name):
				x86Str = x86Str + str(varoff_dict[n.expr.right.name]) + '''(%ebp)'''
			elif isinstance( n.expr.right, Const):
				x86Str = x86Str + '''$''' + str(n.expr.right.value) + ''', %eax
	movl %eax, ''' + str(varoff_dict[n.nodes.name]) + '''(%ebp)'''
	elif isinstance( n, CallFunc ):#print_int_nl instruciton
		if n.node.name == 'print_int_nl':
			if isinstance( n.args[0], Name):
				x86Str = '''
	pushl ''' + str(varoff_dict[n.args[0].name]) + '''(%ebp)'''
			elif isinstance( n.args[0], Const):
				x86Str = '''
	pushl $''' + n.args[0].value 
		x86Str = '''
	call print_int_nl
	addl $4, %esp'''
		
	output.write(x86Str)

def flattened_to_asm(flattened,output):
	global varname_lst
	global varoff_dict
	# Okay, so first we need to set up where variables will be located relative to the ebp(?).
	offset = + 4
	varname_set = set(varname_lst)
	for var in varname_set:
		varoff_dict[var]=-offset
		offset = offset + 4
	# with that now made, we can call flatnode_to_asm to write the actual output.
	output.write('''
.globl main
main:
	pushl %ebp
	movl %esp, %ebp
	subl $'''+str(offset)+''', %esp''')#preparation

	for line in flattened:
		flatnode_to_asm(line,output)

	output.write('''
	movl $0, %eax 
	leave
	ret
''')#clean up

	

parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
parser.add_argument(  'infile', nargs='+', type=argparse.FileType('r'), default=sys.stdin  )
argv = sys.argv
argv.pop(0)
ns = parser.parse_args(argv)
print ns.infile[0].name
for input_file in ns.infile:
	tree = compiler.parse(input_file.read())
	(input_fname,input_ext) = os.path.splitext(input_file.name)
	print 'From'
	print '\t',tree
	flattened = flatten(tree)
	print 'To'
	for line in flattened:
		print '\t', line
	print 'Vars'
	varname_set = set(varname_lst)
	for var in varname_set:
		print '\t',var
	
	outfile = open(input_fname + '.s','w')
	
	flattened_to_asm(flattened,outfile)


