import threading, time, MySQLdb, datetime, pickle
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

		self.users = {}
		self.activeUser = None


		# Establish connection to the database
		self.establishDatabaseConnection(args)

		# Read Hosts
		self.readHosts()

		# Read Users
		self.readUsers()
		
		# Read reservations
		self.readReservations()

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


	def getUniqueHostId(self):
		return max(self.hosts.keys())+1



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


	def readHosts(self):
		self.log.info('Reading Hosts')

		self.log.debug ('Loading Hosts from database')
		self.hosts = {}

		sql = 'SELECT `id`, `pickledData` FROM `hosts`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			hostId = int(row[0])
			host = pickle.loads(row[1])
			host.initializeUnpickableData(self.log)
			self.hosts[hostId] = host
			
	
	def readUsers(self):
		self.log.info('Reading Users')

		self.users = {}
		
		sql = 'SELECT `user_name`, `pickledData` FROM `users`'
		self.cursor.execute(sql)
		
		while True:
			row = self.cursor.fetchone()
			if not row: break

			user = pickle.loads(row[1])
			user.initializeUnpickableData(self.hosts, self.log)
			self.users[row[0]] = user
			self.log.info('User "%s" with components %s loaded' % (user.name, user.getIDs()))

		
	def readReservations(self):
		self.log.info('Reading reservations')
		
		self.reservations = {}
		
		# prepare the query
		query = 'SELECT `id`, `user`, `start`, `end` FROM  `reservations`'
		self.cursor.execute(query)
		results = self.cursor.fetchall()

		for row in results:
			user = self.getUserCreateIfNotExistent(row[1])
			self.reservations[row[0]] = {'user': user, 'start': row[2], 'end': row[3]}
			
		self.log.debug('%d Reservations fetched' % len(self.reservations))

		


	def startAllHosts(self):
		self.log.debug('Start all Hosts')
		for host in self.hosts.values():
			# start in blocking mode i.e
			host.start(blocking=True)
		

	def stopAllHosts(self):
		self.log.info('Disconnecting all Hosts')
		for host in self.hosts.values():
			host.stop()
			host.join()


	# get the user object that belongs to a name
	# create a new user if it does not exist
	def getUserCreateIfNotExistent(self, name):
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
	def stopAllComponents(self, user=None):
		self.log.info('Stopping all components')

		# if None is passed for user, stop all components
		# of every user
		if not user:
			users = self.users.values()
		# if a user is passed, only stop his components
		else:
			users = [user]

		for user in users:
			for comp in user.components():
				if comp.host and comp.host.isConnected():
					comp.stop()
				else:
					self.log.debug('Skipping component "%s", Host is down' % comp.getName())


	def forceStopAllComponents(self, user=None):
		self.log.info('Force Stopping all components of every users')

		if not user:
			users = self.users.values()
		else:
			users = [user]
			
		for user in users:
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.forceStop()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.getName())


	# Terminate: stop first and kill afterwards
	def terminateAllComponents(self, user=None):
		self.log.info('Terminating all components of every user')

		if not user:
			users = self.users.values()
		else:
			users = [user]
			
		for user in users:
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.terminate()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.getName())
		

	# Terminate: stop first and kill afterwards
	def forceTerminateAllComponents(self):
		self.log.info('Force Terminating all components of every users')

		for user in self.users.values():
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.forceTerminate()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.getName())




	def addReservation(self, user, start_date, end_date):
		if not isinstance(end_date, datetime.datetime):
			raise ValueError('End Parameter is not an instance of datetime')
		if not isinstance(start_date, datetime.datetime):
			raise ValueError('Start Parameter is not an instance of datetime')
		
		id = max(self.reservations.keys())+1
		self.reservations[id] = {'user': user, 'start': start_date, 'end':end_date}

		# update the database
		query = "INSERT INTO `reservations` (`id`, `user`, `start`, `end`) VALUES(%s, %s, %s, %s)"
		self.cursor.execute(query, [id, user.name, start_date, end_date])
		return id
		

	def killReservation(self, id, user):
		if not id in self.reservations or not self.reservations[id]:
			raise ValueError('Invalid id passed "%s"' % str(id))
		if not self.reservations[id]['user'] == user:
			raise ValueError('Unauthorized')
			
		del self.reservations[id]

		# update the database
		query = "DELETE FROM `reservations` WHERE `id`=%s"
		self.cursor.execute(query, [id])

		
	def extendReservation(self, id, end_date, user):
		if not isinstance(end_date, datetime.datetime):
			raise ValueError('End Parameter is not an instance of datetime')
		if not id in self.reservations or not self.reservations[id]:
			raise ValueError('Invalid id passed "%s"' % str(id))
		if not self.reservations[id]['user'] == user:
			raise ValueError('Unauthorized')
		
		self.reservations[id]['end'] = end_date

		# update the database
		query = "UPDATE `reservations` SET `end`=%s WHERE id=%s"
		self.cursor.execute(query, [end_date, id])
		
	def getActiveReservation(self):
		now = datetime.datetime.now()
		for reservation in self.reservations.values():
			if reservation['start'] <= now and reservation['end'] > now:
				return reservation
		return None
		
	def run(self):
		self.log.info('ServerThread is running')
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

	#TODO: check for valid mainActino_id !!
	#TODO: put this function into the user class
	# stores a component based on an object given
	def storeComponent(self, data, user):
		#maps temporary ids (negativ ones) to the actual new ids returned by the database
		idMap = {}
		
		id          = int(data['id'])  #negativ for new ones
		parentId    = int(data['parentId']) if data['parentId'] else None #might be None
		hostId      = int(data['hostId'])
		actionsData = data['actions']
		
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
			host = self.hosts[hostId] if hostId in self.hosts else None

			# get a new unique id for this component from the user object
			autoId = user.getUniqueComponentId()
			self.log.debug('Creating a new component with id "%d"' % autoId)
			component = Component(autoId, user.name, host, None, [], self.log)
			
			# remap the temporary id to the new id
			idMap[id] = autoId
			
			user.append(component)
			
			
		# else we need to update the component
		else:
			# is it a valid component
			if not user.hasComponent(id):
				raise ValueError('The passed componentId (%d) is unknown' % id)
			
			component = user.get(id)
			self.log.debug('Updating %s' % str(component))
			
			# cannot update a running component
			if component.isAlive():
				raise ValueError('Cannot update a running component')
				
			# update the component
			component.host = self.hosts[hostId]

		# update the parent
		component.parent = parent
		if parent and component not in parent.children:
			parent.children.append(component)
			
			
		# Now create / update the actions
		# We have to loop through every action first to create and update all actions. We cannot 
		# update the dependency field yet, as we have no valid ids so far. Therefore we need to
		# create the new actions first and map the temporary ids (negative ones) to the actual ids
		# returned by the database
		for actionData in actionsData:
			aId 		= int(actionData['id']) #new actions have a negativ id
			aName		= actionData['name']
			description	= actionData['description']
			url		= actionData['url']
			startCommands	= actionData['startCommands']
			stopCommands	= actionData['stopCommands']
			# compId field is ignored as the action must be part of this component
			
			
			# if an actionId is specified, it must be valid
			if aId > 0 and not component.hasAction(aId):
				raise ValueError('The given actionId is not a valid id for the component [compId=%d, actionId=%d]' % (component.id, aId))

			if aId < 0:
				# only process this action if the id is valid, i.e. the name is set
				# if not set, skip this action entirely. We don't need to delete
				# the action as its newly created (aId <0). Continue with the next action.
				if not aName.strip():
					continue

				# get a new unique id for this action from the component object
				autoId = component.getUniqueActionId()
				
				action = Action(autoId, aName, {}, {}, description, url, self.log)
				action.setComponent(component)
				
				# remap 
				idMap[aId] = autoId
				
				# append the action to the component
				component.appendAction(action)
				
				
			else:
				# if the action name is invalid (empty) but it's old action (aId > 0),
				# delete the action and continue with the other actions afterwards
				if not aName.strip():
					component.deleteAction(aId)
					continue
				
				action = component.getAction(aId)
				action.name = aName
				action.description = description
				action.url = url

				
				

			# Reset all dependencies, those will be set later
			action.resetDependencies()
			

			# If we created a new component, mainAction_id is None for that component. 
			# Set this action (first action) as the main action
			if component.mainAction == None:
				component.mainAction = action
				


			# parse the commands
			for cmd in startCommands+stopCommands:
				isStartCommand = cmd in startCommands
				
 				cId         = int(cmd['id']) # new start commands have a negative index
				commandStr  = cmd['command']
				blocking    = cmd['blocking']
				hideLog	    = cmd['hideLog']
				
				# if it's a valid new command, store it now
				if cId < 0:
					# only proceed if the command name is not empty. Otherwise
					# if the name is empty (indicating the user deleted the command) and it's not yet
					# created (teporary id, < 0), just skip this component
					if commandStr.strip():
						autoId = action.getUniqueCommandId()
						idMap[cId] = autoId
					
						if isStartCommand:
							action.addStartCommand(ShellCommand(autoId, commandStr, blocking, hideLog))
						else:
							action.addStopCommand(ShellCommand(autoId, commandStr, blocking, hideLog))

				
				# else update the existing one
				else:
					if not action.hasCommand(cId):
						raise ValueError('Command specified a parent-action id that doesn\'t match [compId=%d, actionId=%d, commandId=%d]' % (component.id, action.id, cId))

					# if the name is empty indicating that the user wants to delete the command), delete
					# it permanently from the component
					if not commandStr.strip():
						action.deleteCommand(cId)

					# in case it has a valid name, update the action
					else:
						command = action.getCommand(cId)
						command.setCommand(commandStr)
						command.blocking = blocking
						command.hideLog = hideLog
					
			
		# Delete the component if it doesn't have a main action
		if not component.mainAction:
			user.delete(component)
			raise ValueError('The passed component does not declare a main component')


		# Now we cann loop through the dependencies and check whether they are all valid
		for actionData in actionsData:
			actionId      = int(actionData['id'])
			dependencies  = actionData['dependencies']

			if actionId < 0:
				if not actionId in idMap:
					raise ValueError('Action id is negative, but no mapping entry exists [actionId=%s]'  % str(actionId))
				actionId = idMap[actionId]

			if not component.hasAction(actionId):
				raise ValueError('Specified action is not a part of the component [actionId=%s]' % actionId)
			action = component.getAction(actionId)
			
			# make sure every dependency is valid and create the string (ids joined by semicolons)
			for dep in dependencies:
				depId = int(dep) 
				
				# if the action id is negative (i.e. newly created), try to remap
				if depId < 0:
					if not depId in idMap:
						raise ValueError('Action Dependency id is negative, but no mapping entry found. [depId=%d]' % depId)
					depId = idMap[depId]
					
				
				# if the action Id could not be found simply ignore the action, it might
				# belong to an action that was deleted previsously
				# TODO: add some kind of feedback to the user to show a warning etc.
				if not component.hasAction(depId):
					self.log.warn('The action has an invalid dependency [actionId="%d", depId="%d"]' % (actionId, depId))
					pass
#					raise ValueError('Invalid Dependency specified [actionId=%d]' % depId)
				

				# if the component has this action
				else:
					action.appendDependency(component.getAction(depId))

		# Log
		self.log.debug('Successfully updated: %s' % str(component))
					
		# save the user
		self.saveUser(user)
		return idMap


	def saveUser(self, user):
		self.log.debug('Saving the user with components %s' % user.getIDs())
		# Now that everything worked out, update the database
		sql = "UPDATE `users` SET `pickledData`=%s WHERE `user_name`=%s"
		return self.cursor.execute(sql, [pickle.dumps(user), user.name])
			

	def storeHost(self, id, hostname, username, password, port):
		id = int(id)
		port = int(port)
		
		# negative id indicates a new host to create
		if id < 0:
			id = self.getUniqueHostId()
			host = Host(id, hostname, port, username, password, self.log)
			host.start()
			self.hosts[id] = host

			# update the database
			sql = "INSERT INTO `hosts` (`id`, `pickledData`) VALUES (%s, %s)"
			print self.cursor.execute(sql, [host.id, pickle.dumps(host)])


			return host.createJSONObj();
		

		else:
			if not id in self.hosts:
				raise ValueError('Unknown host passed [id="%d"]' % id)

			host = self.hosts[id]

			# go through all components of this user and make sure
			# that no component assigned to that host is running
			for comp in self.activeUser.components():
				if comp.host == host and comp.isAlive():
					raise ValueError('Cannot change host data for running host [id="%d"]' % id)



			# change the host's data first, then reconnect. If we disconnect
			# before changing the data, the thread loop would automatically
			# reconnect
			host.hostname = hostname
			host.port = port
			host.user = username
			host.pw = password
			host.disconnect()

			# Update the database
			sql = "UPDATE `hosts` SET `pickledData`=%s WHERE `id`=%s"
			self.cursor.execute(sql, [pickle.dumps(host), host.id])

			
			return host.createJSONObj()
			
