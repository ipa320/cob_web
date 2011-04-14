import time
from threading import Thread
from .module import Module
from myExceptions.databaseExceptions import CorruptDatabaseError

class Component(Module, Thread):
	
	def __init__(self, rId, username, hostId, host, name, parentId, actions, log):
		Thread.__init__(self)
		Module.__init__(self, rId, username, name, parentId)	
		self.hostId = hostId
		self.actions = actions

		self.alive = False

		self.log = log


		# actions must contain status / start / stop
		if 'status' not in actions or 'start' not in actions or 'stop' not in actions:
			raise CorruptDatabaseError('Component must have at least three actions: status/start/stop')

	def __str__(self):
		return "Component [%s]" % Module.__str__(self)


	# Component.stop should be called anyway, this function is just to make sure we 
	# the connection in any case
	def __del__(self):
		if self.alive:
			self.log.error ('__del__ invoked and component still running: %s' % str(self))
		self.stop()

	def isAlive(self):
		return self.isAlive

	def start(self):
		if not self.alive:
			self.log.debug ('Starting Component %s' % str(self))
			self.alive = True
			Thread.start(self)

	def stop(self):
		if self.alive:
			self.log.debug ('Stopping Component %s' % str(self))
			self.alive = False


	def run(self):
		while self.alive:
			print self.name
			time.sleep(1)
