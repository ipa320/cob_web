
class Module(object):

	def __init__(self, rId, username, name, parentId):
		self.id = int(rId)
		self.username = username
		self.name = name

		self.parentId = None
		if parentId: self.parentId = int(parentId)

		self.parent = None
		self.children = []


	def __str__(self):
		return "Module [id=%d, username=%s, name=%s, parentId=%s]" % (self.id, self.username, self.name, str(self.parentId))
