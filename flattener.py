#!/usr/bin/python2

from compiler import *

temp_var_c = 0

def gen_temp():
	tmp = 't'+temp_var_c
	temp_var_c = temp_var_c + 1
	return tmp

def flatten(n):
	if isinstance(n,Module):
		return flatten(n.node)
	elif isinstance(n,Stmt):
		return ( n, sum( [ flatten(m) for m in n.nodes ] ) )
	elif isinstance(n,Printnl):
		return ( n, flatten(n.nodes[0]) )
	elif isinstance(n,Assign):
		return ( n, sum( [ flatten(m) for m in n.nodes ] + [flatten(n.expr)] ) )
	elif isinstance(n,AssName):
		return ( n, sum( [ flatten(m) for m in n.nodes ] ) )
	elif isinstance(n, Discard):
		return ( n, flatten(n.expr) )
	elif isinstance( n, Const ):
		return ( n, [] )
	elif isinstance(n,Name):
		return ( n, [] )
	elif isinstance( n, Add ):
		(l,ss1) = flatten(n.left)
		(r,ss2) = flatten(n.right)
		t = gen_temp()
		ss3 = [Assign(AssName(t),Add((l,r)))]
		return ( Name( t ) , ss1 + ss2 + ss3 )
	elif isinstance( n, UnarySub ):
		return ( n, flatten(n.expr) )
	elif isinstance( n, CallFunc ):
		return ( n, sum( [ flatten(m) for m in n.args ] ) + [ flatten(n.node) ] )


