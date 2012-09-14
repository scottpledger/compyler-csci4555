#!/usr/bin/python2

import mglobals
from compiler import *
from compiler.ast import *


def gen_temp():

	tmp = 't'+str(mglobals.temp_var_c)
	mglobals.temp_var_c = mglobals.temp_var_c + 1
	mglobals.varname_lst = mglobals.varname_lst + [tmp]
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
		return flatten(n.expr)
	elif isinstance( n, Assign):
		expr_flat = flatten(n.expr)
		mglobals.varname_lst = mglobals.varname_lst + [n.nodes[0].name]
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
		mglobals.varname_lst = mglobals.varname_lst + [n.name]
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


