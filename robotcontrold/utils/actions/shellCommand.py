
class ShellCommand():
	def __init__(self, rId, command, blocking, hideLog):
		self.id = int(rId)
		self.command = command.strip().replace('\r\n','\n')
		self.blocking = blocking
		self.hideLog = hideLog

	def __str__(self):
		return 'Action [id=%d, action_id=%d, command=..., blocking=%s]' % (self.id, self.action.id, str(self.blocking))

	def createJSONObj(self):
		return {
			'id':		self.id,
			# use repr to replace break by \n etc
			'command':	repr(self.command)[1:-1],
			'blocking':	self.blocking,
			'hideLog':	self.hideLog
		}
