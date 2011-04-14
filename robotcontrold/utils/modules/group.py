from module import Module

class Group(Module):

	def __init__(self, rId, user_id, name, actions):
		Module.__init__(self, rId, user_id, name)

	def __str__(self):
		return "Group [Module=%s]" % Module.__str__(self)
