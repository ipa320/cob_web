import time
from threading import Thread
from myExceptions.databaseExceptions import CorruptDatabaseError

class Component():
	
	def __init__(self, rId, username, host, mainAction, parentId, actions, log):
		self.id = int(rId)
		self.username = username
		self.host = host
		self.mainAction = mainAction

		# parentId might be None for groups
		self.parentId = int(parentId) if parentId else None

		# actions may be None (e.g. for "groups")
		# but be careful, actions must be empty in that case as well
		# actions are sorted by id
		self.actions = actions or {}

		self.log = log

		# better solution needed
		if len(self.actions) and not self.host:
			raise CorruptDatabaseError('Component has actions but no host. %s' % str(self))


		for action in self.actions.values():
			action.setComponent(self)


		self.children = []
		self.parent = None
		
		
	def getName(self):
		return self.mainAction.name



	def __str__(self):
		return "Component [id=%d, username=%s, host_id=%s, name=%s, parent_id=%s]" % (self.id, self.username, str(self.host.id) if self.host else 'None', self.getName(), str(self.parentId))


	# Component.stop should be called anyway, this function is just to make sure we 
	# the connection in any case
	def __del__(self):
		for action in self.actions.values():
			if action.isAlive():
				self.log.error ('__del__ invoked and component still running: %s' % str(self))
			self.stop()
			break

	def isAlive(self):
		for action in self.actions.values():
			if action.isAlive():
				return True
		return False




	# stop stops all actions
	def stop(self):
		for action in self.actions.values():
			try:
				action.stop()
			except Exception as e:
				self.log.exception('Exception occured trying to stop: %s' % str(self))

	# force all actions to stop
	def forceStop(self):
		for action in self.actions.values():
			try:
				action.forceStop()
			except Exception as e:
				self.log.exception('Exception occured trying to forceStop %s' % str(self))



	# kill: closes the screen (kill -9)
	def kill(self):
		for action in self.actions.values():
			try:
				action.kill()
			except Exception as e:
				self.log.exception('Exception occured trying to kill: %s' % str(self))

	# force kill all actions
	def forceKill(self):
		for action in self.actions.values():
			try:
				action.forceKill()
			except Exception as e:
				self.log.exception('Exception occured trying to forceKill: %s' % str(self))


	def terminate(self):
		self.stop()
		self.kill()

	def forceTerminate(self):
		self.forceStop()
		self.forceKill()

	
	# lost connection to host. No need to try to shutdown any actions
	def lostConnection(self):
		for action in self.actions.values():
			action.lostConnection()



	# get an action by name. Returns None if not found
	def getAction(self, actionId):
		if not actionId in self.actions:
			return None

		return self.actions[actionId]

	# 
	def hasAction(self, actionId):
		return actionId in self.actions
		
	def appendAction(self, action):
		self.actions[action.id] = action
