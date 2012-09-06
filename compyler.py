#!/usr/bin/python2

import sys
import argparse
import compiler
from compiler import *

parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
parser.add_argument(  'infile', nargs='+', type=argparse.FileType('r'), default=sys.stdin  )
argv = sys.argv
argv.pop(0)
ns = parser.parse_args(argv)

for input_file in ns.infile:
	tree = compiler.parse(input_file.read())
	print tree
