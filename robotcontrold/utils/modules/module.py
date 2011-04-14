
class Module(object):

	def __init__(self, rId, user_id, name):
		self.id = rId
		self.user_id = user_id

		self.name = name

	def __str__(self):
		return "Module [id=%d, user_id=%d, name=%s]" % (self.id, self.user_id, self.name)
