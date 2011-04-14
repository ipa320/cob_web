class Action():
	def __init__(self, rId, name, ref_id, script, args):
		self.id = int(rId)
		self.name = name
		self.ref_id = int(ref_id)
		self.script = script
		self.args = args

	def __str__(self):
		return 'Action [id=%d, ref_id=%d, name=%s, script=%s, args=%s]' % (self.id, self.ref_id, self.name, self.script, self.args)
