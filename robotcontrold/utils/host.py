import time, socket
from threading import Thread
from network.ssh import SSH
from network.screenReader import ScreenReader
from network import ping
from utils.eventHistory import EventHistory
from myExceptions.databaseExceptions import CorruptDatabaseError
from myExceptions.networkExceptions import NoConnectionToHostException


class Host(Thread):
	
	def __init__(self, rId, hostname, port, user, pw, log):
		self.id = int(rId)
		self.hostname = hostname
		self.port = int(port)
		# username
		self.user = user
		self.pw = pw

		# ??
		self._components = []
		
		self.initializeUnpickableData(log)
		
	# initialize all the data that doesn't get pickled
	# this function has to be called when getting an object from memcahed
	# to initialize the missing data
	def initializeUnpickableData(self, log):
		if not hasattr(self, '_initialized'):
			Thread.__init__(self)
			self._initialized = True
			
			self.log = log
			self.alive = False
			self.ssh = SSH(self)
			self.ctrlChannel = None
			self.screenReader = None
		
		
	def __getstate__(self):
		return {
			'id': self.id,
			'hostname': self.hostname,
			'port': self.port,
			'user': self.user,
			'pw': self.pw,
		}
			

	def __str__(self):
		return "Host [id=%d, hostname=%s, port=%d, user=%s]" % (self.id, self.hostname, self.port, self.user)



	def isConnected(self):
		return self.ssh and self.ssh.isConnected()


	def isAlive(self):
		return self.alive

	def appendComp(self, comp):
		self._components.append(comp)

	#@Override
	def start(self, blocking=False):		
		if not self.alive:
			self.log.debug('Starting %s' % str(self))
			self.alive = True

			if blocking:
				self.connect()

			Thread.start(self)

	def stop(self):
		if self.alive:
			# put self.alive = False ontop
			self.alive = False			
			self.disconnect()
			self.log.debug('Stopping %s' % str(self))


	def invokeShell(self):
		if not self.ssh:
			raise NoConnectionToHostException('SSH is not connected!')
		return self.ssh.invokeShell()

	def exec_command(self, cmd):
		if not self.ssh:
			raise NoConnectionToHostException('SSH is not connected!')
		return self.ssh.exec_command(cmd)


	# Connect / Disconnect are usually not called from outside but from the run method
	def connect(self):
		if not self.isConnected():
			try:
				self.ssh.connect()
			except socket.timeout as e:
				self.log.debug('Connection to %s timed out' % str(self))
				return False
			except Exception as e:
				self.log.debug('Could not connect to %s' % str(self))
				return False

			try:
				self.log.info('Connected to %s' % str(self))
				EventHistory.hostOnline(self)
				return True

			except Exception as e:
				self.log.exception('Could open control. Clossing %s' % str(self))
				self.screenReader = None
				self.disconnect()
				return False




	def disconnect(self):
		if self.isConnected():
			try:
				self.log.debug('Closing ControlChannel')
				self.ssh.disconnect()
				self.log.info('Disconnected from %s' % str(self))
			except Exception as e:
				self.log.exception('Could not disconnect from %s\n' % str(self))
		


	def run(self):
		while self.alive:
			if not self.isConnected():
				if not self.connect():
					# wait a certain amount of time before trying to reconnect
					time.sleep(5)
			else:
				try:
					delay = ping.do_one(self.hostname, 2)
					if delay is None:
						self.log.debug('Ping timed out, we probably lost the connection')
						self.lostConnection()
					#i,o,e = self.ssh.exec_command('uptime')
					#print 'O: %s\tE: %s' % (o.read().strip(), e.read().strip())
				except Exception as e:
					print "* EXCEPTION :"
					self.lostConnection()

			time.sleep(1)


	def lostConnection(self):
		self.log.warning('Lost connection to %s' % str(self))
		self.log.info ('Informing all components assigned to this host')
		EventHistory.hostOffline(self)

		for comp in self._components:
			comp.lostConnection()

		self.ctrlChannel = None
		self.screenReader = None
		self.ssh.disconnect()


	# Used for the webserver to send infomration to the client
	def createJSONObj(self):
		return {
			'id':       self.id,
			'hostname': self.hostname,
			'user':	    self.user,
			'port':	    self.port
		}
	

