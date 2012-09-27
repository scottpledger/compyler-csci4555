#!/usr/bin/python2

import mglobals
from compiler import *
from compiler.ast import *

class TempName(Node):
	def __init__(self, name, lineno=None):
		self.name = name
		self.lineno = lineno

	def getChildren(self):
		return self.name,

	def getChildNodes(self):
		return ()

	def __repr__(self):
		return "TempName(%s)" % (repr(self.name),)

def gen_temp():

	tmp = TempName('t'+str(mglobals.temp_var_c))
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
		n_node = Name(n.nodes[0].name)
		mglobals.varname_lst = mglobals.varname_lst + [n_node]
		return ( Name(n.nodes[0].name) , expr_flat[1] + [Assign(n_node, expr_flat[0])])
	elif isinstance( n, Add ):
		( l, ss1 ) = flatten( n.left  )
		( r, ss2 ) = flatten( n.right )
		t = gen_temp()
		ss3 = [ Assign(t, Add((l,r))) ]
		return ( t , ss1 + ss2 + ss3 )
	elif isinstance( n, Const ):
		return ( n, [] )
	elif isinstance( n, Name ):
		mglobals.varname_lst = mglobals.varname_lst + [n]
		return ( n, [] )
	elif isinstance( n, CallFunc ):
		t = gen_temp()
		return ( t , [Assign(t, n) ] )
	elif isinstance( n, UnarySub ):
		t = gen_temp()
		expr_flat = flatten(n.expr)
		return ( t , expr_flat[1] + [Assign(t, UnarySub( expr_flat[0]))])
	elif isinstance( n, Printnl ):
		nodes_flat = flatten(n.nodes[0])
		return ( None , nodes_flat[1]+[CallFunc(Name('print_int_nl'),[nodes_flat[0]])])


