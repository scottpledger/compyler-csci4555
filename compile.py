#! /usr/local/bin/python

import pdb
import sys
import compiler
import mutils
from compiler.ast import *
from ir_x86 import *
from explicit import PrintASTVisitor2
from heapify import HeapifyVisitor, FreeInFunVisitor
from explicate import ExplicateVisitor2
from type_check2 import TypeCheckVisitor2
from closure_conversion import ClosureConversionVisitor
from flatten import FlattenVisitor4
from instruction_selection import InstrSelVisitor4
from register_alloc import RegisterAlloc3
from print_visitor import PrintVisitor3
from generate_x86 import GenX86Visitor3
from generate_x86 import fun_prefix
from remove_structured_control import RemoveStructuredControl
from uniquify import UniquifyVisitor
from os.path import splitext
from declassify import DeclassifyVisitor

debug = mutils.debug()

try:
#    pdb.set_trace()
    input_file_name = sys.argv[1]
    ast = compiler.parseFile(input_file_name)
    if debug:
      mutils.print_debug('finished parsing')
      mutils.print_debug(ast)
    
    ast = DeclassifyVisitor().preorder(ast)
    if debug:
      mutils.print_debug('finished declassifying')
      mutils.print_debug(ast)

    ast = UniquifyVisitor().preorder(ast)
    if debug:
      mutils.print_debug('finished uniquifying')
      mutils.print_debug(ast)

    ast = ExplicateVisitor2().preorder(ast)
    if debug:
      mutils.print_debug( 'finished explicating')
      mutils.print_debug(PrintASTVisitor2().preorder(ast))
    
      mutils.print_debug('starting to heapify')
    FreeInFunVisitor().preorder(ast)
    ast = HeapifyVisitor().preorder(ast)
    if debug:
      mutils.print_debug('finished heapifying')
      mutils.print_debug(PrintASTVisitor2().preorder(ast))
    
      mutils.print_debug('type checking')
    TypeCheckVisitor2().preorder(ast)

    if debug:
      mutils.print_debug('starting closure conversion')
    ast = ClosureConversionVisitor().preorder(ast)
    if debug:
      mutils.print_debug('finished closure conversion')
      mutils.print_debug(PrintASTVisitor2().preorder(ast))
    
      mutils.print_debug('starting to flatten')
      mutils.print_debug(ast,True)
    instrs = FlattenVisitor4().preorder(ast)
    if debug:
      mutils.print_debug('finished flattening')
      mutils.print_debug(PrintASTVisitor2().preorder(instrs))

    funs = InstrSelVisitor4().preorder(instrs)
    
    if debug:
      mutils.print_debug('finished instruction selection')
    for fun in funs:
        mutils.print_debug(PrintVisitor3().preorder(fun))
    if debug:
      mutils.print_debug('starting register allocation')

    new_funs = []
    for fun in funs:
        mutils.print_debug('register allocating ' + fun.name)
        new_funs += [RegisterAlloc3().allocate_registers(fun,
                                                         input_file_name + '_' + fun.name)]
    funs = new_funs
    mutils.print_debug('finished register allocation')

    for fun in funs:
        fun.code = RemoveStructuredControl().preorder(fun.code)
    mutils.print_debug('finished removing structured control')
    if debug:
        for fun in funs:
            mutils.print_debug( PrintVisitor3().preorder(fun))

    x86 = GenX86Visitor3().preorder(Stmt(funs))
    mutils.print_debug('finished generating x86')

    asm_file = open(splitext(input_file_name)[0] + '.s', 'w')
    print >>asm_file, ('.globl %smain' % fun_prefix) + x86

except EOFError:
    print "Could not open file %s." % sys.argv[1]
except Exception, e:
    print e
    raise
    exit(-1)

