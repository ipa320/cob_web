import threading, time, MySQLdb, datetime
from utils.host import Host
from utils.actions.action import Action
from utils.actions.shellCommand import ShellCommand
from myExceptions.databaseExceptions import CorruptDatabaseError
from utils.component import Component
from utils.user import User
from utils.eventHistory import EventHistory




class ServerThread(threading.Thread):
	def __init__(self, log, args):
		threading.Thread.__init__(self)
		self.alive = False

		self.log = log
		self.users = None
		self.hosts = None
		self.conn = None
		self.cursor = None

		self.activeUser = None
		self.reservations = {}#None


		# Establish connection to the database
		self.establishDatabaseConnection(args)

		# Read User
		self.readUsers()

		# Read Hosts
		self.readHosts()

		# Read components
		self.readComponents()

		# Connect to Hosts
		self.startAllHosts()
		
		# quit all components that might be running
		self.forceTerminateAllComponents()
		



	# self.stop should be called anyway, but just be be sure
	def __del__(self):
		self.stop()

	
	# @Override 
	def start(self):
		if not self.alive:
			self.log.info('Starting ServerThread')
			self.alive = True
			threading.Thread.start(self)

	def stop(self):
		if self.alive:
			self.log.info('Stopping ServerThread')
			if self.cursor:
				try: self.cursor.close()
				except Exception as e: pass
			if self.conn:
				try: self.conn.close()
				except Exception as e: pass


			self.forceTerminateAllComponents()
			self.stopAllHosts()

			self.alive = False

	def isAlive(self):
		return self.alive



	def establishDatabaseConnection(self, args=[]):
		if not 'mysqlDb' in args:
			raise TypeError('mysqlDb must be passed as argument')

		self.log.info('Establishing Mysql Connection')
		mysqlHost = 'localhost'
		mysqlUser = 'root'
		mysqlPasswd = ''

		if 'mysqlHost' in args:
			mysqlHost = args['mysqlHost']
		if 'mysqlUser' in args:
			mysqlUser = args['mysqlUser']
		if 'mysqlPw' in args:
			mysqlPasswd = args['mysqlPw']
		mysqlDb = args['mysqlDb']


		self.conn = MySQLdb.connect (host=mysqlHost, user=mysqlUser, passwd=mysqlPasswd, db=mysqlDb)
		self.cursor = self.conn.cursor()


	def readUsers(self):
		self.log.info ('Reading Users')
		
		self.log.debug ('Loading Users from database')
		self.users = {}
		sql = 'SELECT DISTINCT `user_name` FROM `components`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			# usernames always in lowercase!
			self.users[row[0].lower()] = User(row[0])


		self.log.debug ('%d users found' % len(self.users))


	def readHosts(self):
		self.log.info('Reading Hosts')


		self.log.debug ('Loading Hosts from database')
		self.hosts = {}
		sql = 'SELECT `id`,`hostname`,`port`,`user`,`pw` FROM `hosts`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			hostId = row[0]
			self.hosts[hostId] = Host(*row, log=self.log)
			


	def readComponents(self):
		self.log.info('Reading Components')

		self.log.debug ('Loading ShellCommands from database')
		shellCommands = {}
		sql = 'SELECT `id`, `action_id`, `type`, `command`, `blocking` FROM `shellCommands`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			rId = int(row[0])
			action_id = int(row[1])
			rType = row[2] #type is either start or stop
			cmd = row[3]
			blocking = row[4] == 'Y'

			if not action_id in shellCommands:
				shellCommands[action_id] = {'start':{}, 'stop': {}}

			shellCommands[action_id][rType][rId] = ShellCommand(rId, cmd, blocking)



		self.log.debug ('Loading ComponentActions from database')
		actionsByCompAndName = {}
		actionsById = {}
		sql = 'SELECT `id`, `name`, `comp_id`, `dependencies`, `description` FROM `componentActions`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			rId = int(row[0])
			name = row[1]
			compId = row[2]
			dependencyIds = row[3].split(';') if row[3] else []
			description = row[4];

			# actions can have several start/stop commands assigned (start / stop). But they don't have to.
			startCmds = shellCommands[rId]['start'] if rId in shellCommands else {}
			stopCmds =  shellCommands[rId]['stop']  if rId in shellCommands else {}
			
			# create an associative array to store all actions sorted by compId -> rId
			# two actions of one component must not have the same name
			if not compId in actionsByCompAndName:
				actionsByCompAndName[compId] = {}

			# create a new action and assign it to the two arrays.
			# The first one is sorted by compId -> id, the second by id only (used for searching dependencies)
			action = Action(rId, name, startCmds, stopCmds, dependencyIds, description, self.log)
			actionsByCompAndName[compId][rId] = action
			actionsById[rId] = action

		
		self.log.debug ('Sorting ComponentActions by dependencies')
		for action in actionsById.values():
			for depId in action.dependencyIds:
				depId = int(depId)
				if not depId in actionsById:
					raise CorruptDatabaseError('Dependency "%d" for action ("%s", id:"%d") not found' % (depId, action.name, action.id))

				action.appendDependency(actionsById[depId])



		self.log.debug ('Loading Components from database')
		sql = 'SELECT `id`, `user_name`, `name`, `parent_id`, `host_id` FROM `components`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			# pop the last element. isGroup == Y for groups
			compId = int(row[0])
			username = row[1]
			name = row[2]
			parentId = row[3] # int or None
			hostId = row[4]
			

			# compActions may be none
			compActions = actionsByCompAndName[compId] if compId in actionsByCompAndName else []

			# compHost may be None for groups
			compHost = self.hosts[hostId] if hostId in self.hosts else None

			comp = Component(compId, username, compHost, name, parentId, compActions, self.log)
			self.users[username].append(comp)
			if compHost:
				compHost.appendComp(comp)

			self.log.debug('%s added to user %s' % (str(comp), username))



		self.log.debug ('Sorting components (parents)')
		for user in self.users.values():

			for currentComp in user.components():
				if currentComp.parentId:
					if not user.get(currentComp.parentId):
						raise CorruptDatabaseError('Parent for Component %s not found' % str(currentComp))
					
					parent = user.get(currentComp.parentId)

					currentComp.parent = parent
					parent.children.append(currentComp)



	def startAllHosts(self):
		self.log.debug('Start all Hosts')
		for host in self.hosts.values():
			# start in blocking mode
			host.start(blocking=True)
		

	def stopAllHosts(self):
		self.log.info('Disconnecting all Hosts')
		for host in self.hosts.values():
			host.stop()
			host.join()


	# get the user object that belongs to a name
	# create a new user if it does not exist
	def getUserCreateIfNotExistent(self, name):
		if not isinstance(name, basestring):
			raise ValueError('Name must be a string')
		
		# username must be in the users array
		if not name in self.users:
			user = User(name)
			self.users[name] = user
		else:
			user = self.users[name]
		return user
		


	# The server can only be user if registered for a certain user.
	# You can either pass a user object or a string
	# Passing a valid user causes the server to log out the currently active user and log in the new user
	# Passing None caueses the server to log out the currently active user and do nothing 
	def prepareServerForNewUser(self, user):
		username = ''
		if user is None:
			user = None
		elif isinstance(user, User):
			user = self.getUserCreateIfNotExistent(user.name)
		elif isinstance(user, basestring):
			user = self.getUserCreateIfNotExistent(user)
		else:
			raise ValueError('User must be either None, a User Class or a string')

		

		if self.activeUser:
			self.log.info('Logging current user out: %s' % self.activeUser.name)

		if user:
			self.log.info('Preparing the Server for new user: %s' % username)

		self.forceTerminateAllComponents()
		
		# Clear the eventHistory
		EventHistory.clear()
		
		self.activeUser = user


	# Same as prepareServerForNewUser(None)
	def removeActiveUser(self):
		self.prepareServerForNewUser(None)


	# It would be enough to stop the components of the active user only, but 
	# let's stop them all, to be sure
	def stopAllComponents(self):
		self.log.info('Stopping all components')

		for user in self.users.values():
			for comp in user.components():
				if comp.host and comp.host.isConnected():
					comp.stop()
				else:
					self.log.debug('Skipping component "%s", Host is down' % comp.name)


	def forceStopAllComponents(self):
		self.log.info('Force Stopping all components of every users')

		for user in self.users.values():
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.forceStop()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.name)


	# Terminate: stop first and kill afterwards
	def terminateAllComponents(self):
		self.log.info('Terminating all components of every user')

		for user in self.users.values():
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.terminate()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.name)
		

	# Terminate: stop first and kill afterwards
	def forceTerminateAllComponents(self):
		self.log.info('Force Terminating all components of every users')

		for user in self.users.values():
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.forceTerminate()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.name)




	def addReservation(self, user, start_date, end_date):
		if not isinstance(end_date, datetime.datetime):
			raise ValueError('End Parameter is not an instance of datetime')
		if not isinstance(start_date, datetime.datetime):
			raise ValueError('Start Parameter is not an instance of datetime')
		
		id = len(self.reservations)
		self.reservations[id] = {'user': user, 'start': start_date, 'end':end_date}
		return id
		
	def killReservation(self, id, user):
		if not id in self.reservations or not self.reservations[id]:
			raise ValueError('Invalid id passed "%s"' % str(id))
		if not self.reservations[id]['user'] == user:
			raise ValueError('Unauthorized')
			
		self.reservations[id] = None
		
	def extendReservation(self, id, end_date, user):
		if not isinstance(end_date, datetime.datetime):
			raise ValueError('End Parameter is not an instance of datetime')
		if not id in self.reservations or not self.reservations[id]:
			raise ValueError('Invalid id passed "%s"' % str(id))
		if not self.reservations[id]['user'] == user:
			raise ValueError('Unauthorized')
		
		self.reservations[id]['end'] = end_date
		
	def getActiveReservation(self):
		now = datetime.datetime.now()
		for reservation in self.reservations.values():
			if reservation['start'] <= now and reservation['end'] > now:
				return reservation
		return None
		
	def run(self):
		activeReservation = None
		while self.alive:
			try:
				activeReservation = self.getActiveReservation()
				if not activeReservation:
					if self.activeUser:
						self.prepareServerForNewUser(None)
				else:
					if activeReservation['user'] != self.activeUser:
						self.prepareServerForNewUser(activeReservation['user'])
				
					
				time.sleep(3)
			except Exception as e:
				print ("Exception occured: " + str(e))

		
		self.stop()

	
	# stores a component based on an object given
	def storeComponent(self, data, user):
		#maps temporary ids (negativ ones) to the actual new ids returned by the database
		idMap		= {}
		
		id			= int(data['id'])  #negativ for new ones
		name		= data['name']
		parentId	= int(data['parentId']) if data['parentId'] else None #might be None
		hostId		= int(data['hostId'])
		actions		= data['actions']
		
		# check if it's a valid hostId and parentId
		if not hostId in self.hosts:
			raise ValueError('The passed hostId (%d) is unknown' % hostId)
			
		# check if it's a valid parentId
		parent = None
		if parentId:
			if not user.hasComponent(parentId):
				raise ValueError('The passed parentId (%d) is unknown' % parentId)
			parent = user.get(parentId)
		
		
		
		# if id is negative, create a new component
		if id < 0:
			component = None #...
			#idMaps ...
			pass
			
		# else we need to update the component
		else:
			# is it a valid component
			if not user.hasComponent(id):
				raise ValueError('The passed componentId (%d) is unknown' % id)
			
			component = user.get(id)
			
			# cannot update a running component
			if component.isAlive():
				raise ValueError('Cannot update a running component')
				
			# update the component
			component.host = self.hosts[hostId]
			component.name = name
			component.parent = parent
			
			# Update the database
			sql = "UPDATE `components` SET `host_id`=%s, `parent_id`=%s, `name`=%s WHERE `id`=%s"
			self.cursor.execute(sql, [hostId, parentId, name, component.id])
			
			
		# Now create / update the actions
		# We have to loop through every action first to create and update all actions. We cannot 
		# update the dependency field yet, as we have no valid ids so far. Therefore we need to
		# create the new actions first and map the temporary ids (negative ones) to the actual ids
		# returned by the database
		for action in actions:
			aId 			= int(action['id']) #new actions have a negativ id
			aName			= action['name']
			description		= action['description']
			startCommands	= action['startCommands']
			stopCommands	= action['stopCommands']
			# compId field is ignored as the action must be part of this component
			
			# if an actionId is specified, it must be valid
			if aId > 0 and not component.hasAction(aId):
				raise ValueError('The given actionId is not a valid id for the component [compId=%d, actionId=%d]' % (component.id, aId))

			if aId < 0:
				# idMaps ...
				action = None # ...
				pass
				
			else:
				action = component.getAction(aId)
				action.name = aName
				action.description = description
				
				sql = "Update `componentActions` SET `name`=%s, `description`=%s, `dependencies`=%s WHERE `id`=%s"
				self.cursor.execute(sql, [action.name, action.description, None, action.id])
				

			# parse the startCommands
			for cmd in startCommands:
 				cId			= int(cmd['id']) # new start commands have a negative index
				commandStr	= cmd['command']
				blocking	= cmd['blocking']
				
				# create new
				if cId < 0:
					# idMap ...
					# add it to the action
					pass
				
				# update existing
				else:
					if not action.hasCommand(cId):
						raise ValueError('Command specified a parent-action id that doesn\'t match [compId=%d, actionId=%d, commandId=%d]' % (component.id, action.id, cId))
					
					command = action.getCommand(cId)
					command.command = commandStr
					command.blocking = blocking
					
					sql = "UPDATE `shellCommands` SET `command`=%s, `blocking`=%s WHERE `id`=%s"
					self.cursor.execute(sql, [commandStr, 'Y' if blocking else 'N', cId])
			


		# Now we cann loop through the dependencies and check whether they are all valid
		for action in actions:
			dependencies	= action['dependencies']

			
			# make sure every dependency is valid and create the string (ids joined by semicolons)
			depString = ''
			depArray = []
			for dep in dependencies:
				actionId = int(dep['actionId']) 
				compId   = int(dep['compId'])
				
				# if the action id is negative (i.e. newly created), try to remap
				if actionId < 0:
					if not actionId in idMaps:
						raise ValueError('Action id is negative, but no mapping entry found. [compId=%d, actionId=%d]' % (compId, actionId))
					actionId = idMaps[actionId]
					
				# if the comp id is negative (i.e.  newly created), try to remap
				if compId < 0:
					if not compId in idMaps:
						raise ValueError('CompId id is negative, but no mapping entry found. [compId=%d, actionId=%d]' % (compId, actionId))
					compId = idMaps[compId]
				
				
				# if the action Id could not be found
				if not user.hasComponent(compId) or not user.get(compId).hasAction(actionId):
					raise ValueError('Invalid Dependency specified [compId=%d, actionId=%d]' % (compId, actionId))
				
				depString += actionId + ';'
				depArray.append(dep)
			
			# remove trailing ;
			depString.strip(';')

			
			# Now that we've checked the dependencies, udpate the database again
