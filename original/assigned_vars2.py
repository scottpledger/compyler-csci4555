from assigned_vars import AssignedVars

class AssignedVars2(AssignedVars):

    def visitIf(self, n):
        return self.dispatch(n.tests[0][1]) | self.dispatch(n.else_)

    def visitWhile(self, n):
        return self.dispatch(n.body)
