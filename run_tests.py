#! /usr/bin/python
from optparse import OptionParser
import sys
import os
import subprocess
import difflib
from os.path import splitext

""" getTerminalSize()
 - get width and height of console
 - works on linux,os x,windows,cygwin(windows)
"""

__all__=['getTerminalSize']


def getTerminalSize():
   import platform
   current_os = platform.system()
   tuple_xy=None
   if current_os == 'Windows':
       tuple_xy = _getTerminalSize_windows()
       if tuple_xy is None:
          tuple_xy = _getTerminalSize_tput()
          # needed for window's python in cygwin's xterm!
   if current_os == 'Linux' or current_os == 'Darwin' or  current_os.startswith('CYGWIN'):
       tuple_xy = _getTerminalSize_linux()
   if tuple_xy is None:
       print "default"
       tuple_xy = (80, 25)      # default value
   return tuple_xy

def _getTerminalSize_windows():
    res=None
    try:
        from ctypes import windll, create_string_buffer

        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12

        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    except:
        return None
    if res:
        import struct
        (bufx, bufy, curx, cury, wattr,
         left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
        return sizex, sizey
    else:
        return None

def _getTerminalSize_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
       import subprocess
       proc=subprocess.Popen(["tput", "cols"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
       output=proc.communicate(input=None)
       cols=int(output[0])
       proc=subprocess.Popen(["tput", "lines"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
       output=proc.communicate(input=None)
       rows=int(output[0])
       return (cols,rows)
    except:
       return None


def _getTerminalSize_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,'1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (env['LINES'], env['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])

import string
from string import split
# since I don't have colors...
blue   = '\033[94m'
green  = '\033[92m'
yellow = '\033[93m'
red    = '\033[91m'
normal = '\033[0m'
colors = [blue,green,yellow,red,normal]

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
    tests += sorted([d+'/'+f for f in os.listdir(d)])

if options.testfile is not None:
  for f in options.testfile:
    tests += [f]

tests = filter(lambda t: splitext(t)[1] == '.py', tests)
tests = map(lambda t: './' + splitext(t)[0], tests)

success = 0
fail = 0

successes = []
failures = []

STAT_NONE = -2
STAT_PROGRESS = -1

COMPILE_SUCCESS=0
COMPILE_WARN=1
COMPILE_FAIL=2

LINK_SUCCESS=0
LINK_WARN=1
LINK_FAIL=2

RUN_SUCCESS=0
RUN_FAIL=1
terminal_width,terminal_height = getTerminalSize()

def hr():
    print '='*terminal_width

def show_result_line(name,str1,str2,str3,replaceable=False):
    line_begin = name
    line_end = ' '+str1+' '+str2+' '+str3+' '
    test_string = line_begin+line_end
    
    for c in colors:
        test_string = test_string.replace(c,'')
    str_len=len(test_string)
    spaces = terminal_width - str_len
    line_output = line_begin + ' '*spaces + line_end
    if replaceable:
      sys.stdout.write(line_output+'\r')
    else:
      sys.stdout.write(line_output+'\n')
    sys.stdout.flush()

def show_test_result(test_name, compile, link, run, replaceable=False):
    test_output = blue + test_name + normal
    if compile == STAT_NONE:
        compile_result_str = '      '
    elif compile == STAT_PROGRESS:
        compile_result_str = '[    ]'
    elif compile == COMPILE_SUCCESS:
        compile_result_str = '[ ' + green + 'OK' + normal + ' ]'
    elif compile == COMPILE_WARN:
        compile_result_str = '[' + yellow + 'WARN' + normal + ']'
    else:
        compile_result_str = '[' + red + 'FAIL' + normal + ']'
    
    if link == STAT_NONE:
        link_result_str = '      '
    elif link == STAT_PROGRESS:
        link_result_str = '[    ]'
    elif link == COMPILE_SUCCESS:
        link_result_str = '[ ' + green + 'OK' + normal + ' ]'
    elif link == COMPILE_WARN:
        link_result_str = '[' + yellow + 'WARN' + normal + ']'
    else:
        link_result_str = '[' + red + 'FAIL' + normal + ']'

    if run == STAT_NONE:
        run_result_str = '      '
    elif run == STAT_PROGRESS:
        run_result_str = '[    ]'
    elif run == RUN_SUCCESS:
        run_result_str = '[ ' + green + 'OK' + normal + ' ]'
    else:
        run_result_str = '[' + red + 'FAIL' + normal + ']'

    show_result_line(test_output,compile_result_str,link_result_str,run_result_str,replaceable)


#print 'Test Name                         [Comp] [Link] [Run!]'
show_result_line('Test Name','[Comp]','[Link]','[Run!]')


for test_name in tests:
    compile_result = STAT_NONE
    linker_result  = STAT_NONE
    run_result     = STAT_NONE
    test_pyfile    = test_name+'.py'
    test_asmfile   = test_name+'.s'
    test_binfile   = test_name+'.bin'
    test_infile    = test_name+'.in'
    test_expfile   = test_name+'.expected'
    test_experr    = test_name+'.exp.err'
    test_outfile   = test_name+'.bin.out'
    test_errfile   = test_name+'.bin.err'
    test_compout   = test_name+'.cmp.out'
    test_comperr   = test_name+'.cmp.err'
    test_linkout   = test_name+'.lnk.out'
    test_linkerr   = test_name+'.lnk.err'
    test_diffout   = test_name+'.diff.out'
    test_differr   = test_name+'.diff.err'
    
    show_test_result(test_name,compile_result,linker_result,run_result,True)
    
    if options.clean:
      if os.path.exists(test_asmfile):
        os.remove(test_asmfile)
      if os.path.exists(test_binfile):
        os.remove(test_binfile)
      if os.path.exists(test_expfile):
        os.remove(test_expfile)
    
    compile_cmd = [compiler,test_asmfile]
    linker_cmd  = [linker,  test_binfile]
    
    compile_result = STAT_PROGRESS
    show_test_result(test_name,compile_result,linker_result,run_result,True)
    
    compile_proc = subprocess.Popen(compile_cmd,stdout=open(test_compout,'w'),stderr=open(test_comperr,'w'))
    warn = compile_proc.communicate()[1]
    retcode = compile_proc.poll()

    compile_result = COMPILE_SUCCESS
    if retcode != 0:
        compile_result = COMPILE_FAIL
        fail = fail + 1
    elif warn:
        compile_result = COMPILE_WARN
    show_test_result(test_name,compile_result,linker_result,run_result,True)
    
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
        show_test_result(test_name,compile_result,linker_result,run_result,True)
        
        if retcode==0:
            if not os.path.exists(test_expfile):
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
                run_result = RUN_FAIL
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