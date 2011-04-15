import time
from threading import Thread
from .module import Module
from myExceptions.databaseExceptions import CorruptDatabaseError

class Component(Module):
	
	def __init__(self, rId, username, hostId, host, name, parentId, actions, log):
		Module.__init__(self, rId, username, name, parentId)	
		self.hostId = hostId
		self.host = host
		self.actions = actions

		self.log = log

		# better solution needed
		for actionName, action in self.actions.iteritems():
			action.setHost(self.host)


	def __str__(self):
		return "Component [Module=%s]" % Module.__str__(self)


	# Component.stop should be called anyway, this function is just to make sure we 
	# the connection in any case
	def __del__(self):
		if self.alive:
			self.log.error ('__del__ invoked and component still running: %s' % str(self))
		self.stop()

	def isAlive(self):
		return self.isAlive


	# stop stops all actions
	def stop(self):
		for action in self.actions.values():
			try:
				action.stop()
			except Exception as e:
				self.log.exception('Exception occured stopping %s' % str(self))



	# get an action by name. Returns None if not found
	def get(self, actionName):
		if not actionName in self.actions:
			return None

		return self.actions[actionName]

