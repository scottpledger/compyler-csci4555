#!/usr/bin/python2

import sys
import argparse
import compiler
import compiler.ast
from compiler.ast import *

temp_var_c = 0

def gen_temp():
	global temp_var_c
	tmp = 't'+str(temp_var_c)
	temp_var_c = temp_var_c + 1
	return tmp

def flatten(n):
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
		return ( Name(n.nodes[0].name) , expr_flat[1] + [Assign(n.nodes[0], expr_flat[0])])
	elif isinstance( n, Add ):
		( l, ss1 ) = flatten( n.left  )
		( r, ss2 ) = flatten( n.right )
		t = gen_temp()
		ss3 = [ Assign(AssName(t,'OP_ASSIGN'), Add((l,r))) ]
		return ( Name( t ) , ss1 + ss2 + ss3 )
	elif isinstance( n, Const ) or isinstance( n, Name ):
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

parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
parser.add_argument(  'infile', nargs='+', type=argparse.FileType('r'), default=sys.stdin  )
argv = sys.argv
argv.pop(0)
ns = parser.parse_args(argv)

for input_file in ns.infile:
	tree = compiler.parse(input_file.read())
	print 'From'
	print '\t',tree
	flattened = flatten(tree)
	print 'To'
	for line in flattened:
		print '\t', line
	


