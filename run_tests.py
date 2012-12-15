#! /usr/bin/python
from optparse import OptionParser
import sys
import os
import subprocess
import difflib
from os.path import splitext

import string
from string import split
# since I don't have colors...
blue   = '\033[94m'
green  = '\033[92m'
yellow = '\033[93m'
red    = '\033[91m'
normal = '\033[0m'

python_prog = "/usr/bin/python"

default_prog = "./compile.py"
default_tests_dir = "./test"

parser = OptionParser()
parser.add_option("--clean", default=False, action="store_true", dest="clean", help="whether or not to clean up former files.")

parser.add_option("-t", "--test", dest="testfile", action="append",
                                  help="test file to compile, run, and check", metavar="FILE")
parser.add_option("-d", "--dir", dest="testdir", action="append",
                                  help="test directory of files to compile, run, and check", metavar="FILE")
parser.add_option("-c", "--compiler", default="/usr/bin/make",
                  help="compiler command to use.")
parser.add_option("-l", "--linker", default="/usr/bin/make",
                  help="linker command to use.")


(options,args) = parser.parse_args()

compiler = options.compiler

if not os.path.exists(compiler):
    print "Compiler not found: " + compiler
    sys.exit(1)

linker = options.linker

if not os.path.exists(linker):
    print "Linker not found: " + linker
    sys.exit(1)

tests = []
if options.testdir is not None:
  for d in options.testdir:
    tests += [d+'/'+f for f in os.listdir(d)]

if options.testfile is not None:
  for f in options.testfile:
    tests += [f]

tests = filter(lambda t: splitext(t)[1] == '.py', tests)
tests = map(lambda t: './' + splitext(t)[0], tests)

success = 0
fail = 0

successes = []
failures = []

COMPILE_SUCCESS=0
COMPILE_WARN=1
COMPILE_FAIL=2

LINK_SUCCESS=0
LINK_WARN=1
LINK_FAIL=2

RUN_SUCCESS=0
RUN_FAIL=1


def show_test_result(test_name, compile, link, run):
    terminal_width = 50
    test_output = blue + test_name + normal
    if compile == COMPILE_SUCCESS:
        compile_result_str = '[ ' + green + 'OK' + normal + ' ]'
    elif compile == COMPILE_WARN:
        compile_result_str = '[' + yellow + 'WARN' + normal + ']'
    else:
        compile_result_str = '[' + red + 'FAIL' + normal + ']'
    
    if link == COMPILE_SUCCESS:
        link_result_str = '[ ' + green + 'OK' + normal + ' ]'
    elif link == COMPILE_WARN:
        link_result_str = '[' + yellow + 'WARN' + normal + ']'
    else:
        link_result_str = '[' + red + 'FAIL' + normal + ']'

    if run == RUN_SUCCESS:
        run_result_str = '[ ' + green + 'OK' + normal + ' ]'
    else:
        run_result_str = '[' + red + 'FAIL' + normal + ']'

    spaces = terminal_width - len(test_name) - 3 * len('[    ]') + 2 * len(' ')
    for i in range(spaces):
        test_output += ' '
    test_output += compile_result_str + ' ' + link_result_str + ' ' + run_result_str
    print test_output

def hr():
    print '======================================================='
print 'Test Name                         [Comp] [Link] [Run!]'



for test_name in tests:
    test_pyfile  = test_name+'.py'
    test_asmfile = test_name+'.s'
    test_binfile = test_name+'.bin'
    test_infile  = test_name+'.in'
    test_expfile = test_name+'.expected'
    test_experr  = test_name+'.exp.err'
    test_outfile = test_name+'.bin.out'
    test_errfile = test_name+'.bin.err'
    test_compout = test_name+'.cmp.out'
    test_comperr = test_name+'.cmp.err'
    test_linkout = test_name+'.lnk.out'
    test_linkerr = test_name+'.lnk.err'
    test_diffout = test_name+'.diff.out'
    test_differr = test_name+'.diff.err'
    
    if options.clean:
      if os.path.exists(test_asmfile):
        os.remove(test_asmfile)
      if os.path.exists(test_binfile):
        os.remove(test_binfile)
    
    compile_cmd = [compiler,test_asmfile]
    linker_cmd  = [linker,  test_binfile]

    compile_proc = subprocess.Popen(compile_cmd,stdout=open(test_compout,'w'),stderr=open(test_comperr,'w'))
    warn = compile_proc.communicate()[1]
    retcode = compile_proc.poll()

    compile_result = COMPILE_SUCCESS
    if retcode != 0:
        compile_result = COMPILE_FAIL
        fail = fail + 1
    elif warn:
        compile_result = COMPILE_WARN
    linker_result = LINK_FAIL
    run_result = RUN_FAIL
    
    if retcode==0:
        linker_proc = subprocess.Popen(linker_cmd,stdout=open(test_linkout,'w'),stderr=open(test_linkerr,'w'))
        warn = linker_proc.communicate()[1]
        retcode = linker_proc.poll()

        linker_result = LINK_SUCCESS
        if retcode != 0:
            linker_result = LINK_FAIL
            fail = fail + 1
        elif warn:
            linker_result = LINK_WARN
        
        if retcode==0:
            
            expected = open(test_expfile, 'w')
            if os.path.exists(test_infile):
                infile = open(test_infile, 'r')
                retcode = subprocess.call([python_prog,test_pyfile], stdout=expected, stdin=infile, stderr=open(test_experr,'w'))
            else:
                retcode = subprocess.call([python_prog,test_pyfile], stdout=expected, stderr=open(test_experr,'w'))
            
            outfile = open(test_outfile, 'w')
            if os.path.exists(test_infile):
                infile = open(test_infile, 'r')
                retcode = subprocess.call([test_binfile], stdin=infile, stdout=outfile, stderr=open(test_errfile,'w'),shell=True)
            else:
                retcode = subprocess.call([test_binfile], stdout=outfile,shell=True)
            retcode = subprocess.call(["diff","-w","-B",test_expfile, test_outfile],stdout=open(test_diffout,'w'),stderr=open(test_differr,'w'))
            if retcode == 0:
                success = success + 1
                successes.append(test_name)
                run_result = RUN_SUCCESS
            else:
                fail = fail + 1
                failures.append(test_name)
    show_test_result(test_name, compile_result, linker_result, run_result)

hr()
print '                tests passed: ' + green + str(success) + normal + \
        ', tests failed: ' + red + str(fail) + normal

if False and fail > 0:
    print '\nfailures:'
    for f in failures:
        print red + f + normal
        print blue + 'test program:\n' + normal + open(f + '.py', 'r').read()
        print blue + 'output:\n' + normal + open(f + '.out','r').read()
        print blue + 'expected:\n' + normal + open(f + '.expected','r').read()