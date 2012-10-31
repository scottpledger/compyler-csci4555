import compiler
from compiler.ast import *
from vis import Visitor

class GetTag(Node):
    def __init__(self, arg):
        self.arg = arg
    
    def getChildren(self):
        return [self.arg]

    def getChildNodes(self):
        return [self.arg]

    def __repr__(self):
        return "GetTag(%s)" % repr(self.arg)

class InjectFrom(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
    
    def getChildren(self):
        return [self.arg]

    def getChildNodes(self):
        return [self.arg]

    def __repr__(self):
        return "InjectFrom(%s, %s)" % (self.typ, repr(self.arg))

class ProjectTo(Node):
    def __init__(self, typ, arg):
        self.typ = typ
        self.arg = arg
    
    def getChildren(self):
        return [self.arg]

    def getChildNodes(self):
        return [self.arg]

    def __repr__(self):
        return "ProjectTo(%s, %s)" % (self.typ, repr(self.arg))

class Let(Node):
    def __init__(self, var, rhs, body):
        self.var = var
        self.rhs = rhs
        self.body = body

    def getChildren(self):
        return self.rhs, self.body

    def getChildNodes(self):
        return self.rhs, self.body

    def __repr__(self):
        return "Let(%s, %s, %s)" % \
               (self.var, repr(self.rhs), repr(self.body))

class SetSubscript(Node):
    def __init__(self, container, key, val):
        self.container = container
        self.key = key
        self.val = val
    
    def getChildren(self):
        return self.container, self.key, self.val

    def getChildNodes(self):
        return self.container, self.key, self.val

    def __repr__(self):
        return "SetSubscript(%s, %s, %s)" % \
               (repr(self.container), repr(self.key), repr(self.val))

# How to make these modular?

param_types = {
    'is_true' : ['pyobj'],
    'add' : ['big','big'],
    'equal' : ['big','big'],
    'not_equal' : ['big','big'],
    'create_list' : ['pyobj'],
    'create_dict' : [],
    'input_int' : [],
    'input' : [],    
    'get_attr' : ['pyobj', 'str'],
    'set_attr' : ['pyobj', 'str', 'pyobj'],
    'create_class' : ['pyobj'],
    'create_object' : ['pyobj'],
    'get_class' : ['pyobj'],
    'is_class' : ['pyobj'],
    'has_attr' : ['pyobj', 'str'],
    'get_function' : ['pyobj'],
    'get_receiver' : ['pyobj'],
    'is_bound_method' : ['pyobj'],
    'is_unbound_method' : ['pyobj']
    }

return_type = {
    'is_true' : 'bool',
    'add' : 'big',
    'equal' : 'bool',
    'not_equal' : 'bool',
    'create_list' : 'big',
    'create_dict' : 'big',
    'input_int' : 'pyobj',
    'input' : 'int',
    'get_attr' : 'pyobj',
    'set_attr' : 'pyobj',
    'create_class' : 'big',
    'create_object' : 'big',
    'get_class' : 'big',
    'is_class' : 'bool',
    'has_attr' : 'bool',
    'get_function' : 'big',
    'get_receiver' : 'big',
    'is_bound_method' : 'bool',
    'is_unbound_method' : 'bool'
    }

class TypeCheckVisitor(Visitor):
    
    def visitModule(self, n):
        self.dispatch(n.node, {})

    def visitStmt(self, n, env):
        for s in n.nodes:
            self.dispatch(s, env)

    def visitPrintnl(self, n, env):
        t = self.dispatch(n.nodes[0], env)
        if t != 'pyobj':
            raise TypeError('Printnl expected an argument of type pyobj, not %s' % t)

    def visitAssign(self, n, env):
        lhs_t = self.dispatch(n.nodes[0], env)
        rhs_t = self.dispatch(n.expr, env)
        if lhs_t != rhs_t:
            raise TypeError('Assign: expected lhs (%s : %s) to have same type as rhs (%s : %s)' % (repr(n.nodes[0]), lhs_t, repr(n.expr), rhs_t))

    def visitDiscard(self, n, env):
        self.dispatch(n.expr, env)

    def visitConst(self, n, env):
        return n.value.__class__.__name__

    def visitName(self, n, env):
        return 'pyobj'
#         if n.name in env:
#             return env[n.name]
#         else:
#             raise TypeError('TypeCheck: undefined variable %s' % n.name)

    def visitAssName(self, n, env):
        return 'pyobj'
#         if n.name in env:
#             return env[n.name]
#         else:
#             raise TypeError('TypeCheck: undefined variable %s' % n.name)

    def visitAdd(self, n, env):
        left_t = self.dispatch(n.left, env)
        if left_t != 'int':
            raise TypeError('Left of Add must have type int')
        right_t = self.dispatch(n.right, env)
        if right_t != 'int':
            raise TypeError('Right of Add must have type int')
        return 'int'

    def visitUnarySub(self, n, env):
        expr_t = self.dispatch(n.expr, env)
        if expr_t != 'int':
            raise TypeError('Argument of UnarySub must have type int')
        return 'int'

    def visitCallFunc(self, n, env):
        if not isinstance(n.node, Name):
            raise Exception('only direct calls to named functions')
        for (arg, param_t) in zip(n.args, param_types[n.node.name]):
            arg_t = self.dispatch(arg, env)
            if arg_t != param_t:
                raise TypeError('argument type %s does not match parameter type %s in function call %s' % (arg_t, param_t, repr(n)))

        return return_type[n.node.name]
    
    def visitIfExp(self, n, env):
        test_t = self.dispatch(n.test, env)
        if test_t != 'bool':
            raise TypeError('Condition of %s must have type bool' % repr(n))
        then_t = self.dispatch(n.then, env)
        else_t = self.dispatch(n.else_, env)
        if then_t != else_t:
            raise TypeError('Branches of %s\nmust have same type, %s != %s'
                            % (repr(n), then_t, else_t))
        return then_t

    def visitInjectFrom(self, n, env):
        arg_t = self.dispatch(n.arg, env)
        if arg_t != n.typ:
            raise TypeError('InjectFrom expected argument of type %s, not %s'
                            % (n.typ, arg_t))
        return 'pyobj'

    def visitProjectTo(self, n, env):
        arg_t = self.dispatch(n.arg, env)
        if arg_t != 'pyobj':
            raise TypeError('ProjectTo expected argument of type pyobj, not %s'
                            % arg_t)
        return n.typ

    def visitGetTag(self, n, env):
        arg_t = self.dispatch(n.arg, env)
        if arg_t != 'pyobj':
            raise TypeError('GetTag expected argument of type pyobj, not %s'
                            % arg_t)
        return 'int'

    def visitCompare(self, n, env):
        left_t = self.dispatch(n.expr, env)
        right_t = self.dispatch(n.ops[0][1], env)
        if n.ops[0][0] == 'is':
            if left_t != 'pyobj':
                raise TypeError('Left side of %s must have type pyobj, not %s' % (repr(n), left_t))
            if right_t != 'pyobj':
                raise TypeError('Right side of %s must have type pyobj, not %s' % (repr(n), right_t))
        else:
            if left_t != 'int' and left_t != 'bool':
                raise TypeError('Left side of %s must have type int or bool, not %s' % (repr(n), left_t))
            if right_t != 'int' and right_t != 'bool':
                raise TypeError('Right side of %s must have type int or bool, not %s' % (repr(n), right_t))
        return 'bool'
        
    def visitLet(self, n, env):
        rhs_t = self.dispatch(n.rhs, env)
        body_env = env.copy()
        body_env[n.var] = rhs_t
        body_t = self.dispatch(n.body, body_env)
        return body_t

    def visitSetSubscript(self, n, env):
        c_t = self.dispatch(n.container, env)
        k_t = self.dispatch(n.key, env)
        v_t = self.dispatch(n.val, env)
        return 'pyobj'

    def visitSubscript(self, n, env):
        c_t = self.dispatch(n.expr, env)
        k_t = self.dispatch(n.subs[0], env)
        return 'pyobj'


class PrintASTVisitor(Visitor):
    
    def visitModule(self, n):
        return self.dispatch(n.node)

    def visitStmt(self, n):
        return '{\n' + '\n'.join([self.dispatch(s) for s in n.nodes]) + '\n}'

    def visitPrintnl(self, n):
        return 'print ' + self.dispatch(n.nodes[0])

    def visitAssign(self, n):
        lhs = self.dispatch(n.nodes[0])
        rhs = self.dispatch(n.expr)
        return '%s = %s' % (lhs, rhs)

    def visitDiscard(self, n):
        return self.dispatch(n.expr)

    def visitConst(self, n):
        return repr(n.value)

    def visitName(self, n):
        return n.name

    def visitAssName(self, n):
        return n.name

    def visitAdd(self, n):
        left = self.dispatch(n.left)
        right = self.dispatch(n.right)
        return '(%s + %s)' % (left, right)

    def visitUnarySub(self, n):
        expr = self.dispatch(n.expr)
        return '-%s' % expr

    def visitCallFunc(self, n):
        return self.dispatch(n.node) + '(' + \
               ', '.join([self.dispatch(arg) for arg in n.args]) + ')'
    
    def visitIfExp(self, n):
        test = self.dispatch(n.test)
        then = self.dispatch(n.then)
        else_ = self.dispatch(n.else_)
        return '(if %s then %s else %s)' % (test, then, else_)

    def visitIf(self, n):
        test = self.dispatch(n.tests[0][0])
        then = self.dispatch(n.tests[0][1])
        else_ = self.dispatch(n.else_)
        return 'if %s:\n%s\nelse:\n%s' % (test, then, else_)

    def visitWhile(self, n):
        test = self.dispatch(n.test)
        body = self.dispatch(n.body)
        return 'while %s:\n%s' % (test, body)

    def visitInjectFrom(self, n):
        arg = self.dispatch(n.arg)
        return '<dyn>%s' % arg

    def visitProjectTo(self, n):
        arg = self.dispatch(n.arg)
        return '<%s>%s' % (n.typ, arg)

    def visitGetTag(self, n):
        arg = self.dispatch(n.arg)
        return 'tag(%s)' % arg

    def visitCompare(self, n):
        left = self.dispatch(n.expr)
        right = self.dispatch(n.ops[0][1])
        return '(%s %s %s)' % (left, n.ops[0][0], right)
        
    def visitLet(self, n):
        rhs = self.dispatch(n.rhs)
        body = self.dispatch(n.body)
        return "let %s = %s in\n%s" % (n.var, rhs, body)

    def visitSetSubscript(self, n):
        c = self.dispatch(n.container)
        k = self.dispatch(n.key)
        v = self.dispatch(n.val)
        return '%s[%s] <- %s' % (c, k, v)

    def visitSubscript(self, n):
        c = self.dispatch(n.expr)
        k = self.dispatch(n.subs[0])
        return '%s[%s]' % (c,k)

    def visitList(self, n):
        nodes = [self.dispatch(e) for e in n.nodes]
        return '[%s]' % (', '.join(nodes))

