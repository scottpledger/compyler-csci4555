import sys
import json
import inspect
import os
import pprint

debug_all = False

debug_default = False
debug_mods = {
  'compile':debug_default,
  'ast_printer':debug_default,
  'declassify':debug_default,
  'assigned_vars':debug_default,
  'build_interference':debug_default,
  'closure_conversion':debug_default,
  'compiler_utilities':debug_default,
  'explicate':debug_default,
  'explicit':debug_default,
  'flatten':debug_default,
  'free_vars':debug_default,
  'generate_x86':debug_default,
  'heap':debug_default,
  'heapify':debug_default,
  'instruction_selection':debug_default,
  'ir':debug_default,
  'ir_x86':debug_default,
  'mutils':debug_default,
  'print_visitor':debug_default,
  'priority_queue':debug_default,
  'register_alloc':debug_default,
  'remove_structured_control':debug_default,
  'type_check2':debug_default,
  'uniquify':debug_default,
  'vis':debug_default
}

max_modname_len = min(max([len(k) for k in debug_mods.iterkeys()]),12)

pp = pprint.PrettyPrinter(indent=2,width=(79-max_modname_len))

def prep_modname(modName):
  if len(modName) > max_modname_len:
    dist = int((max_modname_len-2)/2)
    return modName[:dist]+'..'+modName[-dist:]
  else:
    return modName.ljust(max_modname_len)

def print_debug_ln(modName,lineno,line,f=False):
  if f!=False:
    f.write('%s\n' % (line) )
  else:
    print '[%s:%3d] %s' % (prep_modname(modName),lineno, line)

def print_debug_obj(modName,lineno,msg,f=False):
  
  if not isinstance(msg,basestring):
    fmted = pp.pformat(msg)
  else:
    fmted = msg
  for line in fmted.splitlines():
    print_debug_ln(modName,lineno,line,f)
  

def debug(msg=False,force=False):
  frm = inspect.stack()[1]
  mod = inspect.getmodule(frm[0])
  modName,ext = os.path.splitext(mod.__file__)
  dbg = debug_all
  if modName in debug_mods:
    dbg = debug_mods[modName]
  
  if (dbg or force) and msg:
    print_debug_obj(modName,frm[2],msg)
  
  return dbg

def print_debug(msg=False,force=False):
  frm = inspect.stack()[1]
  mod = inspect.getmodule(frm[0])
  modName,ext = os.path.splitext(mod.__file__)
  dbg = debug_all
  if modName in debug_mods:
    dbg = debug_mods[modName]
  
  if (dbg or force) and msg:
    print_debug_obj(modName,frm[2],msg)
  
  return dbg

def write_debug(msg=False,filename='debug_written.txt',force=False):
  f=open(filename,'w')
  frm = inspect.stack()[1]
  mod = inspect.getmodule(frm[0])
  modName,ext = os.path.splitext(mod.__file__)
  dbg = debug_all
  if modName in debug_mods:
    dbg = debug_mods[modName]
  
  if (dbg or force) and msg:
    print_debug_obj(modName,frm[2],msg,f)
  
  return dbg

def write_json_debug(msg=False,filename='debug_written.txt',force=False):
  f=open(filename,'w')
  frm = inspect.stack()[1]
  mod = inspect.getmodule(frm[0])
  modName,ext = os.path.splitext(mod.__file__)
  dbg = debug_all
  if modName in debug_mods:
    dbg = debug_mods[modName]
  
  if (dbg or force) and msg:
    f.write(json.dumps(msg,indent=2))
  
  return dbg

