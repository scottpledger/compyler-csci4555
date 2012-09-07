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
		return ( n, [ flatten(m) for m in n.nodes ] )
	elif isinstance(n,Printnl):
		args = []
		flat = []
		for m in n.nodes:
			(name,flt) = flatten(m)
			args = args + [name]
			flat = flat + [(name,flt)] + flt
		return ( CallFunc(Name('print_int'), args), flat )
	elif isinstance(n,Assign):
		return ( n, [ flatten(m) for m in n.nodes ] + [flatten(n.expr)] )
	elif isinstance(n,AssName):
		return ( n, [] )
	elif isinstance(n, Discard):
		return flatten(n.expr)
	elif isinstance( n, Const ):
		return ( n, [] )
	elif isinstance(n,Name):
		return ( n, [] )
	elif isinstance( n, Add ):
		(l,ss1) = flatten(n.left)
		(r,ss2) = flatten(n.right)
		t = gen_temp()
		ss3 = [Assign(AssName(t,''),Add((l,r)))]
		return ( Name( t ) , ss1 + ss2 + ss3 )
	elif isinstance( n, Sub ):
		(l,ss1) = flatten(n.left)
		(r,ss2) = flatten(n.right)
		t = gen_temp()
		ss3 = [Assign(AssName(t,''),Sub((l,r)))]
		return ( Name( t ) , ss1 + ss2 + ss3 )
	elif isinstance( n, UnarySub ):
		t = gen_temp()
		return ( Name( t ), [flatten(n.expr)] )
	elif isinstance( n, CallFunc ):
		t = gen_temp()
		return ( Name( t ), [ n ] )

parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
parser.add_argument(  'infile', nargs='+', type=argparse.FileType('r'), default=sys.stdin  )
argv = sys.argv
argv.pop(0)
ns = parser.parse_args(argv)

for input_file in ns.infile:
	tree = compiler.parse(input_file.read())
	flattened = flatten(tree)
	print flattened
	


