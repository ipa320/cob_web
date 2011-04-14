
class Action(object):
	
	def __init__(self, rId, name, parent_id, script, args):
		self.id = rId
		self.name = name
		self.parent_id = parent_id
		self.script = script
		self.args = args


