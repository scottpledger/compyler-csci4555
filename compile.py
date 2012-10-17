#! /usr/local/bin/python

import sys
import compiler
from compiler.ast import *
from ir_x86 import *
from flatten1 import FlattenVisitor
from instruction_selection2 import InstrSelVisitor2
from generate_x86_1 import GenX86Visitor
from build_interference import BuildInterferenceVisitor
from register_alloc1 import RegisterAlloc
from print_visitor import PrintVisitor
from vis import Visitor
from os.path import splitext
import mparser

debug = False

try:
    input_file_name = sys.argv[1]
    #ast = compiler.parseFile(input_file_name)
    input_file = file(input_file_name,'wr')
    ast = mparser.parser.parse(input_file.read())
    if debug:
        print 'finished parsing'
    instrs = FlattenVisitor().preorder(ast)
    if debug:
        print 'finished flattening'

    instrs = InstrSelVisitor2().preorder(instrs)
    if debug:
        print 'finished instruction selection'
        print PrintVisitor().preorder(instrs)
        print 'starting register allocation'
        
    instrs = RegisterAlloc().allocate_registers(instrs, input_file_name)
    if debug:
        print 'finished register allocation'
        print PrintVisitor().preorder(instrs)

    x86 = GenX86Visitor().preorder(instrs)
    if debug:
        print 'finished generating x86'

    asm_file = open(splitext(input_file_name)[0] + '.s', 'w')
    print >>asm_file, x86

except EOFError:
    print "Could not open file %s." % sys.argv[1]
except Exception, e:
    print e.args[0]
    exit(-1)

