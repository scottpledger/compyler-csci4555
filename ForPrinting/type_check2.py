import compiler
from compiler.ast import *
from explicit import TypeCheckVisitor, param_types, return_type
from compiler_utilities import *

class TypeCheckVisitor2(TypeCheckVisitor):

    def visitModule(self, n):
        local_vars = []
        for s in n.node.nodes:
            if isinstance(s, Assign) and isinstance(s.nodes[0], AssName):
                local_vars += [s.nodes[0].name]
        env = {}
        for x in local_vars:
            env[x] = 'pyobj'
        self.dispatch(n.node, env)

    def visitCallFunc(self, n, env):
        if isinstance(n.node, Name) and n.node.name in builtin_functions:
            for (arg, param_t) in zip(n.args, param_types[n.node.name]):
                arg_t = self.dispatch(arg, env)
                if arg_t != param_t:
                    raise TypeError('argument %s has type %s which does not match parameter type %s in function call %s' % (repr(arg), arg_t, param_t, repr(n)))
            return return_type[n.node.name]
        else:
            fun_t = self.dispatch(n.node, env)
            if fun_t != 'pyobj':
                raise TypeError('function expected to have type pyobj, not type %s' % fun_t)
            
            for arg in n.args:
                arg_t = self.dispatch(arg, env)
                if arg_t != 'pyobj':
                    raise TypeError('argument expected to have type pyobj, not type %s' % arg_t)
            return 'pyobj'
        
    def visitLambda(self, n, env):
        local_vars = []
        for s in n.code.nodes:
            if isinstance(s, Assign) and isinstance(s.nodes[0], AssName):
                local_vars += [s.nodes[0].name]
        body_env = env.copy()
        for x in n.argnames + local_vars:
            body_env[x] = 'pyobj'
        self.dispatch(n.code, body_env)
        return 'pyobj'

    def visitReturn(self, n, env):
        t = self.dispatch(n.value, env)
        if t != 'pyobj':
            raise TypeError('in return, expected pyobj, not %s' % t)

    def visitIf(self, n, env):
        test_t = self.dispatch(n.tests[0][0], env)
        if test_t != 'bool':
            raise TypeError('Condition of %s must have type bool' % repr(n))
        self.dispatch(n.tests[0][1], env)
        self.dispatch(n.else_, env)

    def visitWhile(self, n, env):
        test_t = self.dispatch(n.test, env)
        if test_t != 'bool':
            raise TypeError('Condition of %s must have type bool' % repr(n))
        self.dispatch(n.body, env)


