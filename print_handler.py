from node_handler import Handler
class PrintHandler(Handler):
	def __init__(self,converter=str):
		Handler.__init__(self)
		self.depth=0
		self.converter=converter
	def print_node(self,value):
		tabs = ''
		for i in range(0,self.depth):
			tabs += "  "
		print tabs + self.converter(value)
	def handleASMModule(self,n):
		self.handle(n.node)
	def handleModule(self,n):
		self.handle(n.node)
	def handleASMStmt(self,n):
		[self.handle(s) for s in n.nodes]
	def handleStmt(self,n):
		[self.handle(s) for s in n.nodes]
	def default(self,node):
	  self.print_node(node)