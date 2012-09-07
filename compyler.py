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
		return [ flatten(m) for m in n.nodes ]
	elif isinstance( n, Add ):
		(l,ss1) = flatten(n.left)
		(r,ss2) = flatten(n.right)
		t = gen_temp()
		ss3 = [Assign(AssName(t,''),Add((l,r)))]
		return ( Name( t ) , ss1 + ss2 + ss3 )
	elif isinstance( n, Const ) or isinstance( n, Name ):
		return ( n, [] )

parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
parser.add_argument(  'infile', nargs='+', type=argparse.FileType('r'), default=sys.stdin  )
argv = sys.argv
argv.pop(0)
ns = parser.parse_args(argv)

for input_file in ns.infile:
	tree = compiler.parse(input_file.read())
	flattened = flatten(tree)
	print 'From'
	print tree
	print 'To'
	print flattened
	


