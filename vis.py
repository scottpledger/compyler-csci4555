###############################################################################
# Visitor
import mutils

debug = True

class Visitor:
    def __init__(self):
        self.node = None
        self._cache = {}

    def default(self, node, *args):
        raise Exception('no visit method for type %s in %s for %s' \
                        % (node.__class__, self.__class__, repr(node)))

    def dispatch(self, node, *args):
        mutils.print_debug( 'dispatching for ' + repr(node.__class__) )
        mutils.print_debug('   ' + repr(node) + ' in ' \
                  + self.__class__.__name__ )
        self.node = node
        klass = node.__class__
        meth = self._cache.get(klass, None)
        if meth is None:
            className = klass.__name__
            meth = getattr(self.visitor, 'visit' + className, self.default)
            self._cache[klass] = meth
        ret = meth(node, *args)
        mutils.print_debug('finished with ' + repr(node.__class__) )
        return ret

    def preorder(self, tree, *args):
        """Do preorder walk of tree using visitor"""
        self.visitor = self
        return self.dispatch(tree, *args)


        """
This class is the same as the above, only it looks through a given class' inheritance
tree before reverting to the default function.
"""
class IVisitor(Visitor):
    def dispatch(self, node, *args):
        mutils.print_debug('dispatching for ' + repr(node.__class__) )
        mutils.print_debug( '   ' + repr(node) + ' in ' \
                  + self.__class__.__name__)
        self.node = node
        klass = node.__class__
        meth = self._cache.get(klass, None)
        if meth is None:
            classList = [] # This is really a stack for the dfs search we're about to perform.
            classList.append(klass)
            
            while len(classList) >0 and meth is None:
                sklass = classList.pop()
                if hasattr(self.visitor, 'visit' + sklass.__name__):
                    meth = getattr(self.visitor,'visit'+sklass.__name__, self.default)
                    classList = []
                else:
                    # Ensures we parse classes _exactly_ like python does -- dfs, ltr.
                    classList = classList + [b for b in reversed(list(sklass.__bases__)) ]
                
            if meth is None:
                meth = self.default
            
            self._cache[klass] = meth
            
        ret = meth(node, *args)
        mutils.print_debug( 'finished with ' + repr(node.__class__) )
        return ret

class MVisitor(Visitor):
    def dispatch(self, node, *args):
      
        if type(node) is list:
          try:
            import multiprocessing as mp
            from multiprocessing import Pool
            
            p = Pool(4)
            return p.map(lambda t: self.dispatch(t,*args),node)
            
          except Exception:
            return [self.dispatch(sn,*args) for sn in node]
        mutils.print_debug( 'dispatching for ' + repr(node.__class__) )
        mutils.print_debug('   ' + repr(node) + ' in ' \
                  + self.__class__.__name__ )
        self.node = node
        klass = node.__class__
        meth = self._cache.get(klass, None)
        if meth is None:
            className = klass.__name__
            meth = getattr(self.visitor, 'visit' + className, self.default)
            self._cache[klass] = meth
        ret = meth(node, *args)
        mutils.print_debug('finished with ' + repr(node.__class__) )
        return ret

class MIVisitor(IVisitor):
    def dispatch(self, node, *args):
        mutils.print_debug('dispatching for ' + repr(node.__class__) )
        mutils.print_debug( '   ' + repr(node) + ' in ' \
                  + self.__class__.__name__)
        self.node = node
        klass = node.__class__
        meth = self._cache.get(klass, None)
        if meth is None:
            classList = [] # This is really a stack for the dfs search we're about to perform.
            classList.append(klass)
            
            while len(classList) >0 and meth is None:
                sklass = classList.pop()
                if hasattr(self.visitor, 'visit' + sklass.__name__):
                    meth = getattr(self.visitor,'visit'+sklass.__name__, self.default)
                    classList = []
                else:
                    # Ensures we parse classes _exactly_ like python does -- dfs, ltr.
                    classList = classList + [b for b in reversed(list(sklass.__bases__)) ]
                
            if meth is None:
                meth = self.default
            
            self._cache[klass] = meth
            
        ret = meth(node, *args)
        mutils.print_debug( 'finished with ' + repr(node.__class__) )
        return ret