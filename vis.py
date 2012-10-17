###############################################################################
# Visitor

debug = False

class Visitor:
    def __init__(self):
        self.node = None
        self._cache = {}

    def default(self, node, *args):
        raise Exception('no visit method for type %s in %s for %s' \
                        % (node.__class__, self.__class__, repr(node)))

    def dispatch(self, node, *args):
        if debug:
            print 'dispatching for ' + repr(node.__class__)
            print '   ' + repr(node) + ' in ' \
                  + self.__class__.__name__
        self.node = node
        klass = node.__class__
        meth = self._cache.get(klass, None)
        if meth is None:
            className = klass.__name__
            meth = getattr(self.visitor, 'visit' + className, self.default)
            self._cache[klass] = meth
        ret = meth(node, *args)
        if debug:
            print 'finished with ' + repr(node.__class__)
        return ret

    def preorder(self, tree, *args):
        """Do preorder walk of tree using visitor"""
        self.visitor = self
        return self.dispatch(tree, *args)
