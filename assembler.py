#!/usr/bin/python2

def instr_selection(s,d):
	if(isinstance(s,Print)):
		s0 = Push(cvt(s.nodes[0],d))
		s1 = Call(print_int_nl)
		s2 = AddInstr(4,Register('esp'))
		return [s0,s1,s2]
