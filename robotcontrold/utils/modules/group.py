from .module import Module

class Group(Module):

	def __init__(self, rId, username, name, parentId):
		Module.__init__(self, rId, username, name, parentId)

	def __str__(self):
		return "Group [Module=%s]" % Module.__str__(self)
