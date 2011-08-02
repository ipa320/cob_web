import threading, time, MySQLdb, datetime
from utils.host import Host
from utils.actions.action import Action
from utils.actions.shellCommand import ShellCommand
from myExceptions.databaseExceptions import CorruptDatabaseError
from utils.component import Component
from utils.user import User
from utils.eventHistory import EventHistory

import memcache, pickle


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
		self.reservations = {}#None


		# Establish connection to the database
		self.establishDatabaseConnection(args)

		# Read Hosts
		self.readHosts()
		#for host in self.hosts.values():
		#	sql = "UPDATE `hosts` SET `pickledData`=%s WHERE `id`=%s"
		#	self.cursor.execute(sql, [pickle.dumps(host), host.id])


		# Read Users
		self.readUsers()
		

#		# Read components
#		self.readComponents()
#		for user in self.users.values():
#			sql = "UPDATE `users` SET `pickledData`=%s WHERE `user_name`=%s"
#			self.cursor.execute(sql, [pickle.dumps(user), user.name])

		# Connect to Hosts
		self.startAllHosts()
		
		# quit all components that might be running
		self.forceTerminateAllComponents()
	
	
		# store all userse in mc
#		for username in  self.users.keys():
#			self.mc.set(username, self.users[username])
#			print 'STORED: %s' % username


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

#	def readComponents(self):
#		self.log.info('Reading Components')
#		
#		sql = "SELECT `user_name`, `host_id`, `parent_id`, `pickledData` FROM `components`"
#		self.cursor.execute(sql)
#		rows = self.cursor.fetchall()
		
	#	# first collect all the componoent data
#		compsData = {}
#		for row in rows:
#			user = self.getUserCreateIfNotExistent(row[0])
#			comp = pickle.loads(row[2])
#			host_id = int(row[1])
#			parent_id = int(row[2])
#			
#			compData[comp.id] = {'comp': comp, 'host_id': host_id, 'parent_id': parent_id, 'children': children}
#			
#			
#		# now iterate through the data again to initialize the components
#		# with the correct host / parent / children 
#		for compData in compsData.values():
#			comp = compData['comp']
#			host_id = compData['host_id']
#			parent_id = compData['parent_id']
#			
#			if not host_id in self.hosts:
#				raise CorruptDatabaseError('The host [id="%d"] associated to the component [id="%d"] could not be found' % (host_id, comp.id))
#			host = self.hosts[host_id]
#				
#			if not parent_id in compsData:
#				raise CorruptDatabaseError('The parent [id="%d"] associated to the component [id="%d"] could not be found' % (parent_id, comp.id))
#			parent = compsData[parent_id]['comp']
#			
#			# initialize the component with the parent
#			comp.initializeUnpickableData(self.hosts[compData['hostId']], 
		
		
	def readComponents(self):
		self.log.info('Reading Components')
		
		sql = "SELECT `id`, `user_name`, `mainAction_id`, `host_id`, `parent_id` FROM `components`"
		self.cursor.execute(sql)
		componentsData = self.cursor.fetchall()
		
		# create the components objects
		components = {}
		parents = {}
		for row in componentsData:
			id 				= int(row[0])
			user_name		= row[1]
			mainAction_id	= int(row[2])
			host_id			= int(row[3]) if row[3] else None
			parent_id		= int(row[4]) if row[4] else None
			
			# fetch all actions assigned to this component
			sql = "SELECT `id`, `name`, `dependencies`, `description`, `url` FROM `componentActions` WHERE `comp_id`=%s"
			self.cursor.execute(sql, [id])
			actionsData = self.cursor.fetchall()
			
			# create the actions objects
			actions = {}
			dependencies = {}
			for row in actionsData:
				actionId 		= int(row[0])
				name			= row[1]
				dependencyIds	= list(int(s) for s in str(row[2]).split(';')) if row[2] else []
				description		= row[3]
				url				= row[4]
				
				
				# fetch all shell commands assigned to this action
				sql = "SELECT `id`, `type`, `command`, `blocking`, `hideLog` FROM `shellCommands` WHERE `action_id`=%s"
				self.cursor.execute(sql, [actionId])
				commandsData = self.cursor.fetchall()
				
				# create the start/stopCommand dicts
				startCommands = {}
				stopCommands = {}
				for row in commandsData:
					commandId 	= int(row[0])
					type		= row[1]
					command		= row[2]
					blocking	= row[3] == 'Y'
					hideLog		= row[4] == 'Y'
					
					if type == 'start':
						startCommands[commandId] = ShellCommand(commandId, command, blocking, hideLog)
					else:
						stopCommands[commandId] = ShellCommand(commandId, command, blocking, hideLog)
						
				
				# Important: do not care about dependencies yet, we'll do that at the end
				# for now, only store the dependencyIds assigend to the action id
				dependencies[actionId] = dependencyIds
						
				# create the action object.
				action = Action(actionId, name, startCommands, stopCommands, description, url, self.log)
				actions[actionId] = action
				
				
			# now check for the dependencys. Note that dependencys can only be set within noe component
			for actionId in dependencies.keys():
				dependencyIds = dependencies[actionId]
				
				for depId in dependencyIds:
					if not depId in actions:
						raise CorruptDatabaseError('The given dependency id "%d" for the action "%d" was not found' % (depId, actionId))
					actions[actionId].appendDependency(actions[depId])
			
			# Check for the mainAction
			if not mainAction_id in actions:
				raise CorruptDatabaseError('The main action "%d" was not found for the component "%d"' % (mainAction_id, id))
			mainAction = actions[mainAction_id]
			
			# Check for the host
			if host_id and host_id not in self.hosts:
				raise CorruptDatabaseError('The host "%d" declared for the component "%d" was not found' % (host_id, id))
			host = self.hosts[host_id] if host_id else None
				

			# Note, parent must be set at the end. Just store the parentId assigend to the component id for now
			if parent_id:
				parents[id] = parent_id
			
			# Create the component object
			component = Component(id, user_name, host, mainAction, actions, self.log)
			components[id] = component
			
			
			# add the component to the user's components
			self.getUserCreateIfNotExistent(user_name).append(component)
		
		
		# Now that all components are created, set the parents
		for id in parents.keys():
			parent_id = parents[id]
		
			# check whether parent_id is valid
			if not parent_id in components:
				raise CorruptDatabaseError('The given parent_id "%d" for component "%d" was not found' % (parent_id, id))
			
			# set parent / child
			component = components[id]
			parent = components[parent_id]
		
			component.setParent(parent)
			parent.appendChild(component)
		

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

	#TODO: check for valid mainActino_id !!	
	# stores a component based on an object given
	def storeComponent(self, data, user):
		import random
		#maps temporary ids (negativ ones) to the actual new ids returned by the database
		idMap		= {}
		
		id			= int(data['id'])  #negativ for new ones
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
			host = self.hosts[hostId] if hostId in self.hosts else None
			component = Component(0, user.name, host, None, [], self.log)
			
			# Note: use None / 0 for main action id. Updating later 
			#sql = "INSERT INTO `components` (`user_name`, `host_id`, `mainAction_id`, `parent_id`) VALUES(%s,%s,%s,%s)"
			#self.cursor.execute(sql, [user.name, host.id if host else None, 0, parent.id if parent else None])
			#autoId = self.cursor.lastrowid
			autoId = int(random.random()*1000)
			
			component.id = autoId
			idMap[id] = autoId
			
			user.append(component)
			
			
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
			component.parent = parent
			
			# Update the database
			#sql = "UPDATE `components` SET `host_id`=%s, `parent_id`=%s WHERE `id`=%s"
			#self.cursor.execute(sql, [hostId, parentId, component.id])
			
			
		# Now create / update the actions
		# We have to loop through every action first to create and update all actions. We cannot 
		# update the dependency field yet, as we have no valid ids so far. Therefore we need to
		# create the new actions first and map the temporary ids (negative ones) to the actual ids
		# returned by the database
		for action in actions:
			aId 			= int(action['id']) #new actions have a negativ id
			aName			= action['name']
			description		= action['description']
			url				= action['url']
			startCommands	= action['startCommands']
			stopCommands	= action['stopCommands']
			# compId field is ignored as the action must be part of this component
			
			
			# if an actionId is specified, it must be valid
			if aId > 0 and not component.hasAction(aId):
				raise ValueError('The given actionId is not a valid id for the component [compId=%d, actionId=%d]' % (component.id, aId))

			if aId < 0:
				action = Action(0, aName, {}, {}, description, url, self.log)
				action.setComponent(component)
				
				#sql = "INSERT INTO `componentActions` (`name`, `comp_id`, `description`) VALUES(%s,%s,%s)"
				#self.cursor.execute(sql, [action.name, component.id, action.description])
				#autoId = self.cursor.lastrowid
				autoId = int(random.random()*1000)
				
				# remap 
				idMap[aId] = autoId
				
				# set the id and append the action to the component
				action.id = autoId
				component.appendAction(action)
				
				
			else:
				action = component.getAction(aId)
				action.name = aName
				action.description = description
				
				#sql = "UPDATE `componentActions` SET `name`=%s, `description`=%s, `dependencies`=%s WHERE `id`=%s"
				#self.cursor.execute(sql, [action.name, action.description, None, action.id])
				

			# If we created a new component, mainAction_id is None for that component. 
			# Set this action (first action) as the main action
			if component.mainAction == None:
				component.mainAction = action
				
				# update the database
				#sql = "UPDATE `components` SET `mainAction_id`=%s WHERE `id`=%s"
				#self.cursor.execute(sql, [action.id, component.id])
				

			# parse the commands
			for cmd in startCommands+stopCommands:
				isStartCommand = cmd in startCommands
				
 				cId			= int(cmd['id']) # new start commands have a negative index
				commandStr	= cmd['command']
				blocking	= cmd['blocking']
				hideLog		= cmd['hideLog']
				
				# if the command is empty, remove it from the databse
				if not commandStr.strip():
					# if the command is new (temporary id < 0), do nothing, as the command was not
					# stored yet anyway
					#if cId > 0:
					#	sql = "DELETE FROM `shellCommands` WHERE `id`=%s"
					#	self.cursor.execute(sql, [cId])
					pass
				
				# if it's a valid new command, store it now
				elif cId < 0:
					#sql = 'INSERT INTO `shellCommands` (`command`, `action_id`, `blocking`, `hideLog`, `type`) VALUES(%s, %s, %s, %s)'
					#self.cursor.execute(sql, [commandStr, action.id, 'Y' if blocking else 'N', 'Y' if hideLog else 'N', 'start' if isStartCommand else 'stop'])
					
					#autoId = self.cursor.lastrowid
					autoId = int(random.random()*1000)
					idMap[cId] = autoId
					
					if isStartCommand:
						action.addStartCommand(ShellCommand(autoId, commandStr, blocking, hideLog))
					else:
						action.addStopCommand(ShellCommand(autoId, commandStr, blocking, hideLog))
					pass
				
				# else update the existing one
				else:
					if not action.hasCommand(cId):
						raise ValueError('Command specified a parent-action id that doesn\'t match [compId=%d, actionId=%d, commandId=%d]' % (component.id, action.id, cId))
					
					command = action.getCommand(cId)
					command.command = commandStr
					command.blocking = blocking
					command.hideLog = hideLog
					
					#sql = "UPDATE `shellCommands` SET `command`=%s, `blocking`=%s, `hideLog`=%s WHERE `id`=%s"
					#self.cursor.execute(sql, [commandStr, 'Y' if blocking else 'N', 'Y' if hideLog else 'N', cId])
			
			
			


		# Now we cann loop through the dependencies and check whether they are all valid
		for action in actions:
			dependencies	= action['dependencies']
			
			# make sure every dependency is valid and create the string (ids joined by semicolons)
			depString = ''
			depArray = []
			for dep in dependencies:
				depId = int(dep) 
				
				# if the action id is negative (i.e. newly created), try to remap
				if depId < 0:
					if not depId in idMaps:
						raise ValueError('Action id is negative, but no mapping entry found. [depId=%d]' % depId)
					depId = idMaps[depId]
					
				
				# if the action Id could not be found
				if not component.hasAction(depId):
					raise ValueError('Invalid Dependency specified [actionId=%d]' % depId)
				
				#TODO	
				#action.appendDependency(component.getActiondepId))
				
				#depString += str(actionId) + ';'
				#depArray.append(dep)
			
			# remove trailing ;
			#depString = depString.strip(';') or None
			
			
			# Now that we've checked the dependencies, udpate the database again
			#sql = 'UPDATE `componentActions` SET `dependencies`=%s WHERE `id`=%s'
			#self.cursor.execute(sql, [depString, action['id']])
			
		return idMap
