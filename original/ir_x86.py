from ir1 import *

class Push(Node):
    def __init__(self, arg):
        self.arg = arg

    def getChildren(self):
        return [arg]

    def getChildNodes(self):
        return [arg]

    def __repr__(self):
        return "Push(%s)" % repr(self.arg)

class Pop(Node):
    def __init__(self, bytes):
        self.bytes = bytes

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "Pop(%s)" % repr(self.bytes)

class PopValue(Node):
    def __init__(self, target):
        self.target = target

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "PopValue(%s)" % repr(self.target)

class CallX86(Node):
    def __init__(self, name):
        self.name = name

    def getChildren(self):
        return []

    def getChildNodes(self):
        return []

    def __repr__(self):
        return "call %s" % self.name

