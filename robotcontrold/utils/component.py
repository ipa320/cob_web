import time
from threading import Thread
from myExceptions.databaseExceptions import CorruptDatabaseError
from utils.host import Host

class Component():
	
	def __init__(self, rId, username, host, mainAction, actions, log):
		self.id = int(rId)
		self.mainAction = mainAction

		# actions may be None (e.g. for "groups")
		# but be careful, actions must be empty in that case as well
		# actions are sorted by id
		# main action is part of actions
		self.actions = actions or {}

		# better solution needed
		if len(self.actions) and not host:
			raise CorruptDatabaseError('Component has actions but no host. %s' % str(self))


		for action in self.actions.values():
			action.setComponent(self)


		self.children = []
		self.parent = None
		
		#
		self.initializeUnpickableData(host, log)
		
		
	def initializeUnpickableData(self, hostObj, log):
		if not hasattr(self, '_initialized'):
			self._initialized = True
			self.log = log
			
			# hostObject must be either an instance of host (e.g. passed
			# directly by init) or it must be a dict (id/host pairs)
			# In the latter case, the attribute _host_id must be key
			# of the dict
			if isinstance(hostObj, Host):
				self.host = hostObj
			elif isinstance(hostObj, dict):
				if not hasattr(self, '_host_id'): raise Exception('Attribute _host_id not set')
				if not self._host_id in hostObj:  raise Exception('_host_id [="%s"] is not in the dict' % str(self._host_id))
				
				self.host = hostObj[self._host_id]
				delattr(self, '_host_id')
			else:
				raise Exception('hostObj must be instance of Host or dict')
			
			# initialize all complex members
			for action in self.actions.values():
				action.initializeUnpickableData(log)
	
	
	# used for pickle in memcached. Exclude certain attributes such as log etc
	def __getstate__(self):
		return {
			'id': self.id,
			'actions': self.actions,
			'mainAction': self.mainAction,
			'parent': self.parent,
			'children': self.children,
			# the following field is added because the host cannot be 
			# pickled with the component. we will remove this field 
			# in the initializeUnpickableData, as soon as we can 
			# get a reference to the actual host using this attribute
			'_host_id': self.host.id
		}
		

	def getUniqueActionId(self):
		return (max(self.actions.keys()) if len(self.actions) > 0 else 0)+1


	def getName(self):
		return self.mainAction.name



	def __str__(self):
		hostId = str(self.host.id) if self.host else 'None'
		parentId = str(self.parent.id) if self.parent else None
		return "Component [id=%d, host_id=%s, name=%s, parent_id=%s]" % (self.id, hostId, self.getName(), parentId)



	def isAlive(self):
		for action in self.actions.values():
			if action.isAlive():
				return True
		return False

	def setParent(self, parent):
		self.parent = parent
		
	def appendChild(self, child):
		self.children.append(child)



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


	def deleteAction(self, actionId):
		if not self.hasAction(actionId):
			raise ValueError('The Action passed does not belong to this component [actionId="%s"]' % str(actionId))

		del self.actions[actionId]

		
	def appendAction(self, action):
		self.actions[action.id] = action


	# used for the webserver
	def createJSONObj(self):
		actionJSONObj = {}
		for action in self.actions.values():
			actionJSONObj[action.id] = action.createJSONObj()
		
		parentId = str(self.parent.id) if self.parent else None
		
		return {
			'host':		self.host.id,
			'name':		self.mainAction.name,
			'parentId':	parentId,
			'actions':	actionJSONObj
		}
