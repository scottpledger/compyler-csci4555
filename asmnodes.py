class ASMNode:
	def __str__( self ):
		return ''
	def __repr__( self ):
		return "ASMNode()"

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

class ASMGlobl(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return '.globl '+str(self.name)
	def __repr__( self ):
		return "ASMGlobl(%r)" % self.name

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

class ASMCall(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'call '+str(self.node)+' '
	def __repr__( self ):
		return "ASMCall(%r)" % self.node

class ASMLabel(ASMNode):
	def __init__(self,name):
		self.name = name
	def __str__( self ):
		return self.name
	def __repr__( self ):
		return "ASMLabel(%r)" % self.name

class ASMMove(ASMNode):
	def __init__(self,src,dest):
		self.left  = src
		self.right = dest
	def __str__( self ):
		return 'movl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMMove(%r,%r)" % (self.left, self.right)

class ASMReg(ASMNode):
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

class ASMStack(ASMNode):
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

class ASMVar(ASMNode):
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
	#def __eq__(self,other):
	#	if isinstance(other,ASMVar):
	#		if self.loc == None or other.loc==None:
	#			return self.name == other.name
	#		else:
	#			return self.name == other.name or self.loc == other.loc
	#	elif isinstance(other,VarName):
	#		return self.name == other
	#	else:
	#		return False
	#def __hash__( self ):
	#	return hash(self.name) ^ hash(self.loc)

class ASMConst(ASMNode):
	def __init__(self,value):
		self.value = value
	def __str__( self ):
		return '$'+str(self.value)
	def __repr__( self ):
		return "ASMConst(%r)" % self.value

class ASMAdd(ASMNode):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'addl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMAdd(%r,%r)" % (self.left, self.right)

class ASMSub(ASMNode):
	def __init__(self,left,right):
		self.left  = left
		self.right = right
	def __str__( self ):
		return 'subl '+str(self.left)+', '+str(self.right)+' '
	def __repr__( self ):
		return "ASMSub(%r,%r)" % (self.left, self.right)

class ASMNeg(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'negl '+str(self.node)+' '
	def __repr__( self ):
		return "ASMNeg(%r)" % self.node

class ASMPush(ASMNode):
	def __init__(self,node):
		self.node = node
	def __str__( self ):
		return 'push '+str(self.node)+' '
	def __repr__( self ):
		return "ASMPush(%r)" % self.node

class ASMLeave(ASMNode):
	def __str__( self ):
		return 'leave '
	def __repr__( self ):
		return 'ASMLeave()'
		

class ASMRet(ASMNode):
	def __str__( self ):
		return 'ret '
	def __repr__( self ):
		return 'ASMRet()'

class ASMComment(ASMNode):
	def __init__(self,comment):
		self.comment = comment
	def __str__( self ):
		return '#'+str(self.comment)
	def __repr__( self ):
		return "ASMComment(%r)" % self.comment
