import collections

class Handler:
	""" This class is inspired by the Visitor class,
	    which bascally does some particular action
	    when a node of some particular class is found,
	    using a function of the form:
	         handle<<ClassName>>(node)."""
	def __init__(self):
		self.node = None
		self._cache = {}
	
	def default(self,node,*args):
		raise Exception('No handler method for type %s in %s for %r' % (node.__class__, self.__class__, node)) 
		
	def handle(self,node,*args):
		self.node = node
		if type(node) is list:
			print "Found a list... %r"%self.__class__.__name__
			return [self.handle(n,*args) for n in node]
		
		nclass = node.__class__
		method = self._cache.get(nclass, None)
		if method is None:
			className = nclass.__name__
			method = getattr(self.visitor, 'handle'+className,self.default)
			self._cache[nclass] = method
		return method(node,*args)
	
	def preorder(self,tree,*args):
		self.visitor = self
		return self.handle(tree,*args)
		
		
