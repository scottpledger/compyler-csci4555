#!/usr/bin/python2

temp_var_c = 0

def gen_temp():
	tmp = 't'+temp_var_c
	temp_var_c = temp_var_c + 1
	return tmp

def flatten(n):
	if isinstance(n,Name):
		return ( n, [] )
	elif isinstance( n, Const ):
		return ( n, [] )
	elif isinstance( n, Add ):
		(l,ss1) = flatten(n.left)
		(r,ss2) = flatten(n.right)
		t = gen_temp()
		ss3 = [Assign(AssName(t),Add((l,r)))]
		return ( Name( t ) , ss1 + ss2 + ss3 )


