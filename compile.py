#!/usr/bin/python2.7

import os
import os.path
import sys
import argparse
import compiler
import compiler.ast
from compiler.ast import *

import mglobals
		
import flattener

import assembler

import mparser

arg_parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
arg_parser.add_argument(  'infile', nargs='+', type=argparse.FileType('r'), default=sys.stdin  )
argv = sys.argv
argv.pop(0)
ns = arg_parser.parse_args(argv)

for input_file in ns.infile:
#	tree = compiler.parse(input_file.read())
	tree = mparser.parser.parse(input_file.read())
	
#	print parser.lexer
#	print tree
	
	(input_fname,input_ext) = os.path.splitext(input_file.name)
#	print 'From'
#	print '\t',tree
	flattened = flattener.flatten(tree)
#	print flattened
#	print 'To'
#	for line in flattened:
#		print '\t', line
#	print 'Vars'
#	mglobals.varname_set = set(mglobals.varname_lst)
#	mglobals.tvarname_set= set(mglobals.tvarname_lst)
#	for var in mglobals.varname_set:
#		print '\t',var
	
	outfile = open(input_fname + '.s','w')
	
	asm_file = assembler.flattened_to_asm(flattened)
	
	#print repr(asm_file)
	
	outfile.write(str(asm_file))


