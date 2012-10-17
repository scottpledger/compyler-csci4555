#!/usr/bin/python2

import mglobals
from compiler import *
from compiler.ast import *
from asmnodes import VarName
from node_handler import Handler


def gen_temp(ntype='temp'):
	tmp = VarName('t'+str(mglobals.temp_var_c),ntype)
	mglobals.temp_var_c = mglobals.temp_var_c + 1
	mglobals.varname_lst = mglobals.varname_lst + [tmp]
	return tmp

class FlattenHandler(Handler):

	def handleModule(self,n):
		return Module(n.doc,self.handle(n.node))
		
	def handleStmt(self,n):
		stmts = []
		for m in n.nodes:
			stmts = stmts + self.handle(m)[1]
		return Stmt(stmts)
	
	def handleDiscard(self,n):
		output = self.handle(n.expr)
		return output
		
	def handleAssign(self,n):
		expr_flat = self.handle(n.expr)
		n_node = VarName(n.nodes[0].name,'user')
		mglobals.varname_lst = mglobals.varname_lst + [n_node]
		return ( VarName(n.nodes[0].name,'user') , expr_flat[1] + [Assign(n_node, expr_flat[0])])
		
	def handleAdd(self,n):
		( l, ss1 ) = self.handle( n.left  )
		( r, ss2 ) = self.handle( n.right )
		t = gen_temp()
		ss3 = [ Assign(t, Add((l,r))) ]
		return ( t , ss1 + ss2 + ss3 )
	
	def handleConst(self,n):
		return ( n, [] )
	
	def handleName(self,n):
		mglobals.varname_lst = mglobals.varname_lst + [n]
		return ( VarName(n.name,'user'), [] )
		
	def handleCallFunc(self,n):
		t = gen_temp()
		return ( t , [Assign(t, n) ] )
		
	def handleUnarySub(self,n):
		t = gen_temp()
		expr_flat = self.handle(n.expr)
		return ( t , expr_flat[1] + [Assign(t, UnarySub( expr_flat[0]))])
		
	def handlePrintnl(self,n):
		nodes_flat = self.handle(n.nodes[0])
		retval = ( None , nodes_flat[1]+[Printnl([nodes_flat[0]],n.dest)] )
		return retval


