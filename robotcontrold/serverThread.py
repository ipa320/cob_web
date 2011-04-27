import threading, time, MySQLdb
from utils.host import Host
from utils.actions.action import Action
from utils.actions.shellCommand import ShellCommand
from myExceptions.databaseExceptions import CorruptDatabaseError
from utils.component import Component
from utils.user import User




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

			self.users[row[0]] = User(row[0])


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
				shellCommands[action_id] = {'start':[], 'stop': []}

			shellCommands[action_id][rType].append(ShellCommand(rId, cmd, blocking))



		self.log.debug ('Loading ComponentActions from database')
		actionsByCompAndName = {}
		actionsById = {}
		sql = 'SELECT `id`, `name`, `comp_id`, `dependencies` FROM `componentActions`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			rId = int(row[0])
			name = row[1]
			compId = row[2]
			dependencyIds = row[3].split(';') if row[3] else []

			startCmds = shellCommands[rId]['start'] if rId in shellCommands else []
			stopCmds =  shellCommands[rId]['stop']  if rId in shellCommands else []
			
			if not compId in actionsByCompAndName:
				actionsByCompAndName[compId] = {}

			action = Action(rId, name, startCmds, stopCmds, dependencyIds, self.log)
			actionsByCompAndName[compId][name] = action
			actionsById[rId] = action

		
		self.log.debug ('Sorting ComponentActions by dependencies')
		for action in actionsById.values():
			for depId in action.dependencyIds:
				depId = int(depId)
				if not depId in actionsById:
					raise CorruptDatabaseError('Dependency "%d" for action ("%s", id:"%d") not found' % (depId, action.name, action.id))

				action.dependencies.append(actionsById[depId])



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




	# The server can only be user if registered for a certain user.
	# You can either pass a user object or a string
	# Passing a valid user causes the server to log out the currently active user and log in the new user
	# Passing None caueses the server to log out the currently active user and do nothing 
	def prepareServerForNewUser(self, user):
		username = ''
		if isinstance(user, User):
			username = user.name
		elif isinstance(user, basestring):
			username = user
		else:
			raise ValueError('User must be either a User Class or a string')

		# username must be in the users array
		if not username in self.users:
			raise ValueError('Unknown user passed')


		if self.activeUser:
			self.log.info('Logging current user out: %s' % self.activeUser.name)

		if user:
			self.log.info('Preparing the Server for new user: %s' % username)

		self.forceTerminateAllComponents()
		self.activeUser = self.users[username]


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
		self.log.info('Force Stopping all components')

		for user in self.users.values():
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.forceStop()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.name)


	# Terminate: stop first and kill afterwards
	def terminateAllComponents(self):
		self.log.info('Terminating all components')

		for user in self.users.values():
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.terminate()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.name)
		

	# Terminate: stop first and kill afterwards
	def forceTerminateAllComponents(self):
		self.log.info('Force Terminating all components')

		for user in self.users.values():
			for comp in user.components():
				if comp.host:
					if comp.host.isConnected():
						comp.forceTerminate()
					else:
						self.log.debug('Skipping component "%s", Host is down' % comp.name)




		
	def run(self):
		while self.alive:
			try:
				time.sleep(1)
			except Exception as e:
				print ("Exception occured: " + str(e))

		
		self.stop()
