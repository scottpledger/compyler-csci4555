#! /usr/local/bin/python

import pdb
import sys
import compiler
from compiler.ast import *
from ir_x86 import *
from explicit2 import PrintASTVisitor2
from heapify import HeapifyVisitor, FreeInFunVisitor
from explicate2 import ExplicateVisitor2
from type_check2 import TypeCheckVisitor2
from closure_conversion import ClosureConversionVisitor
from flatten3 import FlattenVisitor3
from instruction_selection4 import InstrSelVisitor4
from register_alloc3 import RegisterAlloc3
from print_visitor3 import PrintVisitor3
from generate_x86_3 import GenX86Visitor3
from generate_x86_1 import fun_prefix
from remove_structured_control import RemoveStructuredControl
from uniquify import UniquifyVisitor
from os.path import splitext

debug = False

try:
#    pdb.set_trace()
    input_file_name = sys.argv[1]
    ast = compiler.parseFile(input_file_name)
    if debug:
        print 'finished parsing'
        print ast

    ast = UniquifyVisitor().preorder(ast)
    if debug:
        print 'finished uniquifying'
        print ast

    ast = ExplicateVisitor2().preorder(ast)
    if debug:
        print 'finished explicating'
        print PrintASTVisitor2().preorder(ast)
        print 'starting to heapify'
        
    FreeInFunVisitor().preorder(ast)
    ast = HeapifyVisitor().preorder(ast)

    if debug:
        print 'finished heapifying'
        print PrintASTVisitor2().preorder(ast)        
        print 'type checking'
    TypeCheckVisitor2().preorder(ast)

    if debug:
        print 'starting closure conversion'
    ast = ClosureConversionVisitor().preorder(ast)

    if debug:
        print 'finished closure conversion'
        print PrintASTVisitor2().preorder(ast)
        print 'starting to flatten'
    instrs = FlattenVisitor3().preorder(ast)
    if debug:
        print 'finished flattening'
        print PrintASTVisitor2().preorder(instrs)

    funs = InstrSelVisitor4().preorder(instrs)
    if debug:
        print 'finished instruction selection'
        for fun in funs:
            print PrintVisitor3().preorder(fun)
        print 'starting register allocation'

    new_funs = []
    for fun in funs:
        if debug:
            print 'register allocating ' + fun.name
        new_funs += [RegisterAlloc3().allocate_registers(fun,
                                                         input_file_name + '_' + fun.name)]
    funs = new_funs
    if debug:
        print 'finished register allocation'

    for fun in funs:
        fun.code = RemoveStructuredControl().preorder(fun.code)
    if debug:
        print 'finished removing structured control'
        for fun in funs:
            print PrintVisitor3().preorder(fun)

    x86 = GenX86Visitor3().preorder(Stmt(funs))
    if debug:
        print 'finished generating x86'

    asm_file = open(splitext(input_file_name)[0] + '.s', 'w')
    print >>asm_file, ('.globl %smain' % fun_prefix) + x86

except EOFError:
    print "Could not open file %s." % sys.argv[1]
except Exception, e:
    print e.args[0]
    exit(-1)

