#!/usr/bin/python2

import sys
import argparse

parser = argparse.ArgumentParser(description='Translates a .py file to x86 assembly language')
parser.add_argument(  'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin  )
parser.add_argument( 'outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout )
parser.parse_args(sys.argv)


