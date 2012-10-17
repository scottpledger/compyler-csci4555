from compiler.ast import Node
from compiler.ast import Const

class VarName(Node):
	def __init__(self, name, vtype, lineno=None):
		self.name = name
		self.vtype = vtype
		self.lineno = lineno

	def getChildren(self):
		return [self.name]

	def getChildNodes(self):
		return []
	
	def __eq__(self, other):
		if isinstance(other,VarName):
			return self.name == other.name and self.vtype == other.vtype
		else:
			return False
	
	def __hash__(self):
		return hash(self.name) ^ hash(self.vtype)

	def __repr__(self):
		return "VarName(%s,%s)" % (repr(self.name),self.vtype)

class ObjConst(Const):
	def __init__(self,value):
		self.node = value
	def getChildren(self):
		return [self.node]
	def getChildNodes(self):
		return [self.node]

class NumConst(Const):
	def __init__(self,value):
		self.node = value
	def getChildren(self):
		return [self.node]
	def getChildNodes(self):
		return [self.node]

class BoolConst(Const):
	def __init__(self,value):
		self.node = value
	def getChildren(self):
		return [self.node]
	def getChildNodes(self):
		return [self.node]

class ASMNode:
	def __init__(self):
		self.comment = None
	def __str__( self ):
		return ''
	def __repr__( self ):
		return "ASMNode()"
	def getChildren( self ):
		return []

class ASMFile(ASMNode):
	def __init__(self,nodes):
		self.nodes = nodes
	def __str__( self ):
		val = ''
		for n in self.nodes:
			n_str = str(n)
			val += n_str + '\n'			
		return val
	def __repr__( self ):
		return "ASMFile(%r)" % self.nodes
	def getChildren( self ):
		return self.nodes

class ASMGlobl(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return '.globl '+str(self.name)
	def __repr__( self ):
		return "ASMGlobl(%r)" % self.name
	def getChildren(self):
		return [self.name]

class ASMFunc(ASMNode):
	def __init__(self,name,nodes):
		self.name  = name
		self.nodes = [
			ASMPush( ASMReg('ebp') ),
			ASMMove( ASMReg('esp'), ASMReg('ebp') )
		] + nodes + [
			ASMNode(),
			ASMMove( ASMConst(0), ASMReg('eax') ),
			ASMLeave(),
			ASMRet()
		]
	def __str__( self ):
		val = str(self.name) + ':\n'
		for n in self.nodes:
			val += '\t'+str(n)+'\n'
		return val
	def __repr__( self ):
		return "ASMFunc(%r,%r)" % (self.name, self.nodes)
	def getChildren(self):
		return [self.name]+self.nodes

class ASMModule(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return str(self.node)
	def __repr__( self ):
		return "ASMModule(%r)" % ( self.node)
	def getChildren(self):
		return self.node

class ASMStmt(ASMNode):
	def __init__(self,nodes,orig=None):
		self.nodes = nodes
		self.orig = orig
	def __str__( self ):
		val = ''
		for n in self.nodes:
			val += '\t'+str(n)+'\n'
		return val
	def __repr__( self ):
		return "ASMStmt(%r)" % ( self.nodes)
	def getChildren(self):
		return self.nodes
		

class ASMCall(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'call '+str(self.node)+' '
	def __repr__( self ):
		return "ASMCall(%r)" % self.node
	def getChildren(self):
		return [self.node]

class ASMLabel(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return self.name
	def __repr__( self ):
		return "ASMLabel(%r)" % self.name
	def getChildren(self):
		return []



class ASMLoc(ASMNode):
	def getLocation(self):
		raise Exception("Method getLocation not defined for %r!" % self)

class ASMReg(ASMLoc):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return '%'+str(self.name)
	def __repr__( self ):
		return "ASMReg(%r)" % self.name
	def __eq__(self, other):
		return isinstance(other,ASMReg) and other.name == self.name
	def __hash__(self):
		return hash(self.name)
	def getChildren(self):
		return []
	def getLocation(self):
		return self
	

class ASMStack(ASMLoc):
	def __init__(self, reg, offset):
		self.reg = reg
		self.offset = offset
	def __str__( self ):
		return str(self.offset)+'('+str(self.reg)+')'
	def __repr__( self ):
		return "ASMStack(%r,%r)"% (self.reg, self.offset )
	def __eq__(self, other):
		return isinstance(other,ASMStack) and other.reg == self.reg and other.offset == self.offset
	def __hash__(self):
		return hash(self.reg) ^ hash(self.offset)
	def getChildren(self):
		return []
	def getLocation(self):
		return self
		

class ASMVar(ASMLoc):
	def __init__(self,name,loc=None):
		self.name = name
		self.loc  = loc
	def __repr__( self ):
		return "ASMVar(%r,%r)"% (self.name, self.loc )
	def __str__( self ):
		if self.loc != None:
			return str(self.loc)
		print "ERROR!!! Could not convert %r to a string!" % (self)
		return str(self.name)
	def getChildren(self):
		return []
	def getLocation(self):
		return self.loc
		

class ASMConst(ASMLoc):
	def __init__(self,value):
		self.value = value
	def __str__( self ):
		return '$'+str(self.value)
	def __repr__( self ):
		return "ASMConst(%r)" % self.value
	def getChildren(self):
		return []
	def getLocation(self):
		return self

class ASMArithmetic(ASMNode):
	def getSrc(self):
		raise Exception("getSrc not defined for %r"%self)
	def getDest(self):
		raise Exception("getDest not defined for %r"%self)

class ASMMove(ASMArithmetic):
	def __init__(self,src,dest):
		self.left  = src
		self.right = dest
	def __str__( self ):
		return 'movl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMMove(%r,%r)" % (self.left, self.right)
	def getChildren(self):
		return [self.left,self.right]
	def getSrc(self):
		return self.left
	def getDest(self):
		return self.right

class ASMAdd(ASMArithmetic):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'addl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMAdd(%r,%r)" % (self.left, self.right)
	def getChildren(self):
		return [self.left,self.right]
	def getSrc(self):
		return self.right
	def getDest(self):
		return self.left
		

class ASMSub(ASMArithmetic):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'subl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMSub(%r,%r)" % (self.left, self.right)
	def getChildren(self):
		return [self.left,self.right]
	def getSrc(self):
		return self.right
	def getDest(self):
		return self.left

class ASMNeg(ASMArithmetic):
	def __init__(self,node,nde=None):
		self.node = node
	def __str__( self ):
		return 'negl '+str(self.node)+' '
	def __repr__( self ):
		return "ASMNeg(%r)" % self.node
	def getChildren(self):
		return [self.node]
	def getSrc(self):
		return self.node
	def getDest(self):
		return self.node
	
class ASMPush(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'pushl '+str(self.node)+' '
	def __repr__( self ):
		return "ASMPush(%r)" % self.node
	def getChildren(self):
		return [self.node]

class ASMPushVal(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'pushl '+str(self.node)+' '
	def __repr__( self ):
		return "ASMPushVal(%r)" % self.node
	def getChildren(self):
		return [self.node]


class ASMPop(ASMNode):
	def __init__(self,amt):
		self.amt = amt
	def __str__( self ):
		return 'addl $'+str(self.amt)+', %esp '
	def __repr__( self ):
		return "ASMPop(%r)" % self.amt
	def getChildren(self):
		return []

class ASMRet(ASMNode):
	def __str__( self ):
		return 'leave '
	def __repr__( self ):
		return 'ASMLeave()'
	def getChildren(self):
		return []

class ASMLeave(ASMNode):
	def __str__( self ):
		return 'leave '
	def __repr__( self ):
		return 'ASMLeave()'
	def getChildren(self):
		return []

class ASMComment(ASMNode):
	def __init__(self,comment):
		self.comment = comment
	def __str__( self ):
		return '#'+str(self.comment)
	def __repr__( self ):
		return "ASMComment(%r)" % self.comment
	def getChildren(self):
		return []


