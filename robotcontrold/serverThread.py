import threading, time, MySQLdb
from utils.host import Host
from utils.actions.action import Action
from myExceptions.databaseExceptions import CorruptDatabaseError
from utils.modules.component import Component
from utils.modules.group import Group
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


			self.stopAllComponents()
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

		self.log.debug ('Loading HostActions from database')
		actions = {}
		sql = 'SELECT `id`, `name`, `host_id`, `start_script`, `start_arguments`, `stop_script`, `stop_arguments` FROM `hostActions`'
		self.cursor.execute(sql)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			name = row[1]
			hostId = row[2]
			if not hostId in actions:
				actions[hostId] = {}
			actions[hostId][name] = Action(*row, log=self.log)


		self.log.debug ('Loading Hosts from database')
		self.hosts = {}
		sql = 'SELECT `id`,`hostname`,`port`,`user`,`pw` FROM `hosts`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			hostId = row[0]
			if not hostId in actions:
				raise CorruptDatabaseError('No Actions for the host defined. id: %d' % hostId)

			self.hosts[hostId] = Host(*row, actions=actions[hostId], log=self.log)
			


	def readComponents(self):
		self.log.info('Reading Components')

		self.log.debug ('Loading ComponentActions from database')
		actions = {}
		sql = 'SELECT `id`, `name`, `comp_id`, `start_script`, `start_arguments`, `stop_script`, `stop_arguments` FROM `componentActions`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			name = row[1]
			compId = row[2]
			if not compId in actions:
				actions[compId] = {}
			actions[compId][name] = Action(*row, log=self.log)
		

		self.log.debug ('Loading Components from database')
		sql = 'SELECT `id`, `user_name`, `name`, `parent_id`, `host_id`, `is_group` FROM `components`'
		rows = self.cursor.execute(sql)
		self.log.debug ('%d rows fetched' % rows)
		while True:
			row = self.cursor.fetchone()
			if not row: break

			# pop the last element. isGroup == Y for groups
			compId = row[0]
			username = row[1]
			name = row[2]
			parentId = row[3]
			hostId = row[4]
			isGroup = row[5] == 'Y'


			if isGroup:
				if compId in actions: raise CorruptDatabaseError('Actions defined for group. id: %d' % compId)
				group = Group(compId, username, name, parentId)
				self.users[username].append(group)
				self.log.debug('%s added to user %s' % (str(group), username))

			else:
				if not compId in actions: raise CorruptDatabaseError('No Actions for component defined. id: %d' % compId)
				if not hostId in self.hosts: raise CorruptDatabaseError('No Host found for component. id: %d hostId: %d' % (compId, hostId))
				comp = Component(compId, username, hostId, self.hosts[hostId], name, parentId, actions[compId], self.log)
				self.users[username].append(comp)
				self.log.debug('%s added to user %s' % (str(comp), username))



		self.log.debug ('Sorting components (parents)')
		for user in self.users.values():

			for currentComp in user.items():
				if currentComp.parentId:
					if not user.get(currentComp.parentId):
						raise CorruptDatabaseError('Parent for Component %s not found' % str(currentComp))
					
					parent = user.get(currentComp.parentId)

					currentComp.parent = parent
					parent.children.append(currentComp)



	def startAllHosts(self):
		self.log.debug('Start all Hosts')
		for host in self.hosts.values():
			host.start()
		

	def stopAllHosts(self):
		self.log.info('Disconnecting all Hosts')
		for host in self.hosts.values():
			host.stop()




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

		self.stopAllComponents()
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
				comp.stop()



		
	def run(self):
		while self.alive:
			try:
				time.sleep(1)
			except Exception as e:
				print ("Exception occured: " + str(e))

		
		self.stop()
