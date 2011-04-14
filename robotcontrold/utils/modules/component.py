from module import Module

class Component(Module):
	
	def __init__(self, rId, user_id, name, actions):
		Module.__init__(self, rId, user_id, name)
		self.actions = actions

	def __str__(self):
		return "Component [Module=%s, Actions=%s]" % (Module.__str__(self), str(self.actions))
