
class Host():
	
	def __init__(self, rId, ip, vncStartAction, vncStopAction):
		self.id = rId
		self.ip = ip
		self.aVncStart = vncStartAction
		self.aVncStop = vncStopAction

	def __str__(self):
		return "Host [id=%d, ip=%s, aVncStart=%s, aVncStop=%s]" % (self.id, self.ip, self.aVncStart, self.aVncStop)
