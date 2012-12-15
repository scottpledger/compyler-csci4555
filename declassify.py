import compiler
import compiler_utilities
from compiler.ast import *
from compiler.consts import *
from vis import IVisitor
from vis import Visitor
from explicit import Let
import mutils


def get_assignment_node(n):
  if isinstance(n,AssAttr) or isinstance(n,AssName) or isinstance(n,Subscript):
    return n
  if isinstance(n,Function):
    return AssName(n.name,OP_ASSIGN)
  if isinstance(n,Class):
    return AssName(n.name,OP_ASSIGN)
  if isinstance(n,Name):
    return AssName(n.name,OP_ASSIGN)
  if isinstance(n,Getattr):
    return AssAttr(n.expr,n.attrname,OP_ASSIGN)
  return False
    

def get_reference_node(n):
  if isinstance(n,Getattr) or isinstance(n,Name) or isinstance(n,Subscript):
    return n
  if isinstance(n,Function):
    return Name(n.name)
  if isinstance(n,Class):
    return Name(n.name)
  if isinstance(n,AssAttr):
    return Getattr(n.expr,n.attrname)
  if isinstance(n,AssName):
    return Name(n.name)
  return False

def get_assignment_name(n):
  if isinstance(n,Name) or isinstance(n,Function) or isinstance(n,AssName):
    return n.name
  if isinstance(n,AssAttr):
    return n.attrname
    

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
    return [get_assignment_name(n)]

class DeclassifyVisitor(Visitor):
  
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
    an = n.nodes[0]
    if isinstance(n.nodes[0],AssAttr):
      return Discard(CallFunc(Name('set_attr'),[self.dispatch(an.expr,parent,svars),Const(an.attrname),self.dispatch(n.expr,parent,svars)], None,None))
    if get_assignment_name(n.nodes[0]) in svars and not parent==None:
      return Discard(CallFunc(Name('set_attr'),[parent,Const(get_assignment_name(n.nodes[0])),self.dispatch(n.expr,parent,svars)], None,None ))
    elif n in svars and not parent==None:
      return Discard(CallFunc(Name('set_attr'),[parent,Const(get_assignment_name(n.nodes[0])),self.dispatch(n.expr,parent,svars)], None,None ))
    if parent == None:
      
      if isinstance(an,AssAttr):
        return Discard(CallFunc(Name('set_attr'),[an.expr,Const(an.attrname),self.dispatch(n.expr,parent,svars)], None,None))
      else:
        return Assign([self.dispatch(cn,parent,svars) for cn in n.nodes],self.dispatch(n.expr,parent,svars))
    else:
      #we has a parent!
      if(isinstance(an,AssAttr)):
        return Discard(CallFunc(Name('set_attr'),[an.expr,Const(get_assignment_name(an.attrname)),self.dispatch(n.expr,parent,svars)], None,None ))
      else:
        return Assign([self.dispatch(cn,parent,svars) for cn in n.nodes],self.dispatch(n.expr,parent,svars))
    
  def visitAssName(self,n,parent=None,svars=[]):
    if n.name in svars:
      return AssAttr(parent,n.name,n.flags)
    else:
      return n

  def visitFunction(self,n,parent=None,svars=[]):
    if parent==None:
      return Function(n.decorators,n.name,n.argnames,n.defaults,n.flags,n.doc,self.dispatch(n.code,parent,svars))
    elif n.name in svars:
      tmp = compiler_utilities.generate_name('class_func')
      return [Function(n.decorators,tmp,n.argnames,n.defaults,n.flags,n.doc,self.dispatch(n.code,parent,svars)), \
              Discard(CallFunc(Name('set_attr'),[parent,Const(n.name),Name(tmp)], None,None ))]
  
  def visitClass(self,n,parent=None,svars=[]):
    #n.name
    #n.bases
    #n.code
    cvars = DeclassifyBodyFVVisitor().preorder(n.code)
    tmp = compiler_utilities.generate_name('class_var')
    nds = self.dispatch(n.code,Name(tmp),cvars)
    return [Assign([AssName(tmp, 'OP_ASSIGN')], CallFunc(Name('create_class'), [List(n.bases)], None, None))]+\
           [nds] + \
           [Assign([AssName(n.name, 'OP_ASSIGN')],Name(tmp))]
    
  
  def visitConst(self,n,parent=None,svars=[]):
    return n
  
  def visitPrintnl(self,n,parent=None,svars=[]):
    return Printnl([self.dispatch(cn,parent,svars) for cn in n.nodes],n.dest)
  
  def visitGetattr(self,n,parent=None,svars=[]):
    return CallFunc(Name('get_attr'),[self.dispatch(n.expr,parent,svars),Const(n.attrname)],None,None)
  
  def visitNode(self,n,parent=None,svars=[]):
    return n
  
  def visitName(self, n, parent=None, svars=[]):
    if n.name in svars:
      return CallFunc(Name('get_attr'),[parent,Const(n.name)],None,None)
    return n
  
  def visitDiscard(self, n, parent=None, svars=[]):
    return Discard(self.dispatch(n.expr,parent,svars))
  
  def visitCallFunc(self, n, parent=None, svars=[]):
    return CallFunc(self.dispatch(n.node,parent,svars),[self.dispatch(arg,parent,svars) for arg in n.args],n.star_args,n.dstar_args)
  
  def visitSubscript(self, n, parent=None, svars=[]):
    return Subscript(self.dispatch(n.expr,parent,svars),n.flags,n.subs)

  def visitList(self,n,parent=None,svars=[]):
    return List([self.dispatch(cn,parent,svars) for cn in n.nodes])
  
  def visitAdd(self,n,parent=None,svars=[]):
    return Add((self.dispatch(n.left,parent,svars),self.dispatch(n.right,parent,svars)))
  
  def visitSub(self,n,parent=None,svars=[]):
    return Sub((self.dispatch(n.left,parent,svars),self.dispatch(n.right,parent,svars)))
  
  def visitUnarySub(self, n, parent=None, svars=[]):
    return UnarySub(self.dispatch(n.expr,parent,svars))
  
  def visitCompare(self,n,parent=None,svars=[]):
    return Compare(self.dispatch(n.expr,parent,svars),[(cn[0],self.dispatch(cn[1],parent,svars)) for cn in n.ops])
  
  def visitIfExp(self, n, parent=None, svars=[]):
    return IfExp(self.dispatch(n.test,parent,svars),self.dispatch(n.then,parent,svars),self.dispatch(n.else_,parent,svars))
  
  def visitOr(self, n, parent=None, svars=[]):
    return Or([self.dispatch(cn,parent,svars) for cn in n.nodes])
  
  def visitAnd(self, n, parent=None, svars=[]):
    return And([self.dispatch(cn,parent,svars) for cn in n.nodes])
  
  def visitDict(self, n, parent=None, svars=[]):
    return Dict([(self.dispatch(cn[0],parent,svars),self.dispatch(cn[1],parent,svars)) for cn in n.items])
  
  def visitNot(self, n, parent=None, svars=[]):
    return Not(self.dispatch(n.expr,parent,svars))
    
  def visitReturn(self,n,parent=None,svars=[]):
    return Return(self.dispatch(n.value,parent,svars))
  
  def visitWhile(self, n, parent=None, svars=[]):
    if n.else_ is not None:
      return While(self.dispatch(n.test,parent,svars),self.dispatch(n.body,parent,svars),self.dispatch(n.else_,parent,svars))
    return While(self.dispatch(n.test,parent,svars),self.dispatch(n.body,parent,svars),n.else_)
    
  def visitIf(self, n, parent=None, svars=[]):
    return If([(self.dispatch(c,parent,svars),self.dispatch(b,parent,svars)) for c,b in n.tests],self.dispatch(n.else_,parent,svars))
  
  def visitLambda(self,n,parent=None,svars=[]):
    return Lambda(n.argnames,n.defaults,n.flags,self.dispatch(n.code,parent,svars))