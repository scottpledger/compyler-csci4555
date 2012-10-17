#!/usr/bin/python2.7

import os
import os.path
import sys
import argparse
import compiler
import compiler.ast
import pprint
from compiler.ast import *

import mparser
from flattener import FlattenHandler
from instr_sel import InstrSelHandler
from interference import LivenessHandler
from alloc_regs import RegisterAlloc
from print_handler import PrintHandler

arg_parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
arg_parser.add_argument(  'infile', nargs='+', type=argparse.FileType('r'), default=sys.stdin  )
argv = sys.argv
argv.pop(0)
ns = arg_parser.parse_args(argv)
pp = pprint.PrettyPrinter(indent=4,depth=2)
for input_file in ns.infile:
	(input_fname,input_ext) = os.path.splitext(input_file.name)
	
	input_text = input_file.read()
	# ptree = compiler.parse(input_text)  # This might be useful later for debugging...
	mtree = mparser.parser.parse(input_text)	
	
	# Let's flatten this f@#$er...
	instrs = FlattenHandler().preorder(mtree)
	
	
	
	#print "Before:",instrs
	# And select some instructions, I suppose...
	instrs = InstrSelHandler().preorder(instrs)
	#PrintHandler(repr).preorder(instrs)
	
	# And now we have to allocate the registers.
	instrs = RegisterAlloc().allocate_registers(instrs)

