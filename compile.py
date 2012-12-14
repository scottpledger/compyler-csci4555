#! /usr/local/bin/python

import pdb
import os
import sys
import compiler
import mutils
from compiler.ast import *
from ast_printer import ASTPrinter,ASTPyPrinter
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
from generate_x86 import GenX86Visitor4,string_constants
from generate_x86 import fun_prefix
from remove_structured_control import RemoveStructuredControl
from uniquify import UniquifyVisitor
from os.path import splitext
from declassify import DeclassifyVisitor

debug = mutils.debug()

try:
    input_file_name = sys.argv[1]
    fbase = os.path.splitext(input_file_name)[0]
    ast = compiler.parseFile(input_file_name)
    if debug:
      mutils.print_debug('finished parsing')
      mutils.write_debug(repr(ast),fbase+'.prsr.ast')
      mutils.write_debug(ASTPyPrinter().preorder(ast),fbase+'.prsr.apy')
    
    ast = DeclassifyVisitor().preorder(ast)
    if debug:
      mutils.print_debug('finished declassifying')
      mutils.write_debug(repr(ast),fbase+'.dcls.ast')
      mutils.write_debug(ASTPyPrinter().preorder(ast),fbase+'.dcls.apy')

    ast = UniquifyVisitor().preorder(ast)
    if debug:
      mutils.print_debug('finished uniquifying')
      mutils.write_debug(repr(ast),fbase+'.uniq.ast')
      mutils.write_debug(ASTPyPrinter().preorder(ast),fbase+'.uniq.apy')

    ast = ExplicateVisitor2().preorder(ast)
    if debug:
      mutils.print_debug( 'finished explicating')
      mutils.write_debug(PrintASTVisitor2().preorder(ast),fbase+'.expl.pst')
    
      mutils.print_debug('starting to heapify')
      
    FreeInFunVisitor().preorder(ast)
    ast = HeapifyVisitor().preorder(ast)
    if debug:
      mutils.print_debug('finished heapifying')
      mutils.write_debug(PrintASTVisitor2().preorder(ast),fbase+'.heap.pst')
    
      mutils.print_debug('type checking')
    TypeCheckVisitor2().preorder(ast)

    if debug:
      mutils.print_debug('starting closure conversion')
    ast = ClosureConversionVisitor().preorder(ast)
    if debug:
      mutils.print_debug('finished closure conversion')
      mutils.write_debug(PrintASTVisitor2().preorder(ast),fbase+'.clsr.pst')
    
      mutils.print_debug('starting to flatten')
      mutils.write_debug(repr(ast),fbase+'.clsr.ast')
    instrs = FlattenVisitor4().preorder(ast)
    if debug:
      mutils.print_debug('finished flattening')
      mutils.write_debug(PrintASTVisitor2().preorder(instrs),fbase+'.flat.pst')

    funs = InstrSelVisitor4().preorder(instrs)
    
    if debug:
      mutils.print_debug('finished instruction selection')
      count=0
      for fun in funs:
        mutils.write_debug(PrintVisitor3().preorder(fun),fbase+'.isel.'+str(count)+'.pst')
        count+=1
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
      count=0
      for fun in funs:
        mutils.write_debug(PrintVisitor3().preorder(fun),fbase+'.rmsc.'+str(count)+'.pst')
        count+=1

    x86 = GenX86Visitor4().preorder(Stmt(funs))
    mutils.print_debug('finished generating x86')
    
    x86_data = "\n"
    for key in string_constants.keys():
      x86_data += "%s:\n .ascii \"%s\\10\\0\"\n" %(key,string_constants[key])
    
    

    asm_file = open(splitext(input_file_name)[0] + '.s', 'w')
    print >>asm_file, ('%s\n.globl %smain' % (x86_data,fun_prefix)) + x86

except EOFError:
    print "Could not open file %s." % sys.argv[1]
except Exception, e:
    print e
    raise
    exit(-1)

