import compiler
import compiler_utilities
from compiler.ast import *
from compiler.consts import *
from vis import IVisitor
from explicit import Let
import mutils

class DeclassifyBodyFVVisitor(IVisitor):
  def visitStmt(self,n):
    specvars = []
    for cn in n.nodes:
      specvars = specvars + self.dispatch(cn)
    return specvars
  
  def visitFunction(self,n):
    return [n.name]
  
  def visitNode(self,n):
    specvars = []
    for cn in n.getChildNodes():
      specvars = specvars + self.dispatch(cn)
    return specvars
  
  def visitAssName(self,n):
    return [n.name]

class DeclassifyVisitor(IVisitor):
  
  def visitModule(self,n):
    return Module(n.doc,self.dispatch(n.node))
  
  def visitStmt(self,n,parent=None,svars=[]):
    nodes = []
    for cn in n.nodes:
      cd = self.dispatch(cn,parent,svars)
      if type(cd) is list or type(cd) is tuple:
        nodes = nodes + cd
      else:
        nodes.append(cd)
    return Stmt(nodes)
    
  def visitAssign(self,n,parent=None,svars=[]):
    if n.nodes[0].name in svars and not parent==None:
      return Discard(CallFunc(Name('set_attr'),[parent,Const(n.nodes[0].name),self.dispatch(n.expr,parent,svars)], None,None ))
    if parent == None:
      return Assign([self.dispatch(cn,parent,svars) for cn in n.nodes],self.dispatch(n.expr,parent,svars))
    
  def visitAssName(self,n,parent=None,svars=[]):
    if n.name in svars:
      return AssAttr(parent,n.name,n.flags)
    else:
      return n

  def visitFunction(self,n,parent=None,svars=[]):
    if parent==None:
      return n
    elif n.name in svars:
      #return [CallFunc(Name('set_attr'),[parent,Const(n.name),Lambda(n.argnames,n.defaults,n.flags,n.code)])]
      tmp = compiler_utilities.generate_name('class_func')
      return [Function(n.decorators,tmp,n.argnames,n.defaults,n.flags,n.doc,n.code), \
              Discard(CallFunc(Name('set_attr'),[parent,Const(n.name),Name(tmp)], None,None ))]
  
  def visitClass(self,n,parent=None,svars=[]):
    #n.name
    #n.bases
    #n.code
    mutils.print_debug('Code: %r'%n.code,True)
    cvars = DeclassifyBodyFVVisitor().preorder(n.code)
    tmp = compiler_utilities.generate_name('class_var')
    return [Assign([AssName(tmp, 'OP_ASSIGN')], CallFunc(Name('create_class'), list(n.bases), None, None))]+\
           self.dispatch(n.code,Name(tmp),cvars).nodes + \
           [Assign([AssName(n.name, 'OP_ASSIGN')],Name(tmp))]
    
  
  def visitConst(self,n,parent=None,svars=[]):
    return n
