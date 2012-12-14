import mutils
from vis import Visitor,IVisitor
from compiler.ast import Node

class ASTPrinter(IVisitor):
    
  def visitNode(self,n,depth=0):
    strings = []
    for cn in n.getChildren():
      if isinstance(cn,Node):
        strings += [self.dispatch(cn,depth+1)]
      elif cn!=None:
        strings +=[cn]
    
    return {n.__class__.__name__:strings}


def doLine(val,depth,comment=False):
  s=''
  e='\n'
  if depth<0:
    e=''
  if val==None:
    return ''
  for i in range(0,depth):
    s+='  '
  if comment:
    return s+val+' #'+comment+e
  else:
    return s+val+e

class ASTPyPrinter(Visitor):
  
  def visitNode(self,n,depth=0):
    print n
    string=''
    for cn in n.getChildNodes():
      string+= self.dispatch(cn,depth)
    return string
    
  def visitModule(self,n,depth=0):
    string=''
    for cn in n.node.nodes:
      string+= doLine(self.dispatch(cn,depth),depth)
    return string
  
  def visitStmt(self,n,depth=0):
    string=''
    for cn in n.nodes:
      string+= self.dispatch(cn,depth)
    return string
  
  def visitConst(self,n,depth=0):
    if isinstance(n.value,str) or isinstance(n.value,basestring):
      return '\''+n.value+'\''
    return str(n.value)
  
  def visitName(self,n,depth=0):
    return str(n.name)
  
  def visitCallFunc(self,n,depth=0):
    string= self.dispatch(n.node,0)
    
    string+='('
    count=0
    for b in n.args:
      if count!=0:
        string+= ', '
      else:
        count+=1
      string+= self.dispatch(b,-1)
    string+=')'
    return doLine(string,depth)
  
  def visitIf(self,n,depth=0):
    string = ''
    count=0
    for t,b in n.tests:
      mstring = 'if '
      if count!=0:
        mstring= 'elif '
      else:
        count+=1
      mstring+= self.dispatch(t,-1)
      mstring = doLine(mstring+' :',depth)
      mstring+= self.dispatch(b,depth+1)
      string += mstring
    if n.else_ is not None:
      string += doLine('else:',depth)
      string += self.dispatch(n.else_,depth+1)
    return string
  
  def visitFunction(self,n,depth=0):
    string = 'def '+n.name+'('
    count=0
    for b in n.argnames:
      if count!=0:
        string+= ', '
      else:
        count+=1
      string+= b
    string += '):'
    string = doLine(string,depth)
    string += self.dispatch(n.code,depth+1)
    return string
  
  def visitClass(self,n,depth=0):
    string = 'class '+n.name+'('
    count=0
    for b in n.bases:
      if count!=0:
        string+= ', '
      else:
        count+=1
      string+= b
    string += '):'
    string = doLine(string,depth)
    string += self.dispatch(n.code,depth+1)
    return string
  
  def visitDiscard(self,n,depth=0):
    return self.dispatch(n.expr,depth)
  
  def visitSubscript(self,n,depth=0):
    string = self.dispatch(n.expr,depth)
    for b in n.subs:
      string += '['+self.dispatch(b,-1)+']'
    return doLine(string,depth)
  
  def visitGetattr(self,n,depth=0):
    return doLine(self.dispatch(n.expr,depth)+'.'+n.attrname,depth)
  
  def visitAssName(self,n,depth=0):
    return doLine(n.name,depth)
  
  def visitAssAttr(self,n,depth=0):
    return doLine(self.dispatch(n.expr,depth)+'.'+n.attrname,depth)
  
  def visitAssign(self,n,depth=0):
    string =''
    count=0
    for b in n.nodes:
      if count!=0:
        string+= ' = '
      else:
        count+=1
      string+= self.dispatch(b,-1)
    return doLine(string + ' = ' + self.dispatch(n.expr,-1) , depth)
  
  def visitPrintnl(self,n,depth=0):
    string ='print '
    count=0
    for b in n.nodes:
      if count!=0:
        string+= ', '
      else:
        count+=1
      string+= self.dispatch(b,-1)
    return doLine(string , depth)
  
  def visitAdd(self,n,depth=0):
    return doLine(self.dispatch(n.left,-1)+' + '+self.dispatch(n.right,-1),depth)
  
  def visitWhile(self,n,depth=0):
    string = 'while '+self.dispatch(n.test,-1)+':'
    string = doLine(string,depth)
    string += self.dispatch(n.body,depth+1)
    return string
  def visitReturn(self,n,depth=0):
    return doLine('return '+self.dispatch(n.value,-1),depth)
  
  def visitIfExp(self,n,depth=0):
    return doLine(self.dispatch(n.then,-1)+' if '+self.dispatch(n.test,-1)+' else '+self.dispatch(n.else_,-1),depth)
  
  def visitUnarySub(self,n,depth=0):
    return doLine('-'+self.dispatch(n.expr,-1),depth)
  
  def visitAnd(self,n,depth=0):
    string='('
    count=0
    for b in n.nodes:
      if count!=0:
        string+= ' and '
      else:
        count+=1
      string+= self.dispatch(b,-1)
    string+=')'
    return doLine(string,depth)
  
  def visitOr(self,n,depth=0):
    string='('
    count=0
    for b in n.nodes:
      if count!=0:
        string+= ' or '
      else:
        count+=1
      string+= self.dispatch(b,-1)
    string+=')'
    return doLine(string,depth)
  
  def visitList(self,n,depth=0):
    string='['
    count=0
    for b in n.nodes:
      if count!=0:
        string+= ', '
      else:
        count+=1
      string+= self.dispatch(b,-1)
    string+=']'
    return doLine(string,depth)
  
  def visitNot(self,n,depth=0):
    return doLine('not '+self.dispatch(n.expr,-1),depth)
  
  def visitCompare(self,n,depth=0):
    string = '( '+self.dispatch(n.expr,-1)
    for a,b in n.ops:
      string += ' ' + a + ' ' + self.dispatch(b,-1)
    return doLine(string,depth)
  
  def visitDict(self,n,depth=0):
    string='{'
    count=0
    for a,b in n.items:
      if count!=0:
        string+= ', '
      else:
        count+=1
      string+= self.dispatch(a,-1) + ': ' + self.dispatch(b,-1)
    string+='}'
    return doLine(string,depth)
  
  def visitLambda(self,n,depth=0):
    string = 'lambda'
    for a in n.argnames:
      string+= ' '+a
    string += ': ' + self.dispatch(n.code,-1)
    return doLine(string,depth)