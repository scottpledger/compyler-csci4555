#!/usr/bin/python2

import sys
import argparse
import compiler
from compiler import *

parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
parser.add_argument(  'infile', nargs='+', type=argparse.FileType('r'), default=sys.stdin  )
ns = parser.parse_args(sys.argv)

for infile in ns.infile:
	tree = compiler.parse(infile.read())
	print tree
