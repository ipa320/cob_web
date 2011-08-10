
class ShellCommand():
	def __init__(self, rId, command, blocking, hideLog):
		self.id = int(rId)
		self.setCommand(command)
		self.blocking = blocking
		self.hideLog = hideLog

	def __str__(self):
		return 'Action [id=%d, action_id=%d, command=..., blocking=%s]' % (self.id, self.action.id, str(self.blocking))

	def setCommand(self, commandStr):
		self.command = commandStr.strip().replace('\r\n', '\n')

	def createJSONObj(self):
		return {
			'id':		self.id,
			'command':      self.command,
			'blocking':	self.blocking,
			'hideLog':	self.hideLog
		}
