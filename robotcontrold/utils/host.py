import time
from threading import Thread
from network.ssh import SSH
from network.screenReader import ScreenReader
from myExceptions.databaseExceptions import CorruptDatabaseError
from myExceptions.networkExceptions import NoConnectionToHostException


class Host(Thread):
	
	def __init__(self, rId, hostname, port, user, pw, log):
		Thread.__init__(self)

		self.id = int(rId)
		self.hostname = hostname
		self.port = int(port)
		self.user = user
		self.pw = pw

		self.log = log

		self.ssh = None
		self.ctrlChannel = None
		self.screenReader = None

		self.alive = False
		self._components = []
		

	def __str__(self):
		return "Host [id=%d, hostname=%s, port=%d, user=%s]" % (self.id, self.hostname, self.port, self.user)


	# As usually just to be safe
	def __del__(self):
		if self.isConnected():
			self.log.error('__del__ invoked and host still running: %s' % str(self))
		self.disconnect()



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
				self.ssh = SSH(self)
				self.ssh.connect()
				self.ctrlChannel = self.invokeShell()

				# kill possible old controlScreens
				self.ctrlChannel.send('screen -X -S controlScreen kill\n')
				self.ctrlChannel.send('screen -S controlScreen\n')
				self.screenReader = ScreenReader('Host #%d' % self.id, self.ctrlChannel, self.log)
				self.screenReader.start()
				self.log.info('Connected to %s' % str(self))
			except Exception as e:
				self.log.exception('Could not connect to %s' % str(self))


	def disconnect(self):
		if self.isConnected():
			try:
				self.log.debug('Closing ControlChannel')
				try: self.ctrlChannel.send('exit\n')
				except Exception as e:
					self.log.exception('Could not close ControlChannel')

				# wait for screen reader to be closed
				if self.screenReader and self.screenReader.isAlive():
					self.log.debug('Joining ScreenReader for "Host #%d"' % self.id)
					self.screenReader.join()

				self.ssh.disconnect()
				self.log.info('Disconnected from %s' % str(self))
			except Exception as e:
				self.log.exception('Could not disconnect from %s\n' % str(self))
		


	def run(self):
		conn = False
		while self.alive:
			print "self.isConnected: %s\tconn: %s" % (str(self.isConnected()), str(conn))
			if (self.ctrlChannel):
				print 'status: %s\t%s' % (self.ctrlChannel.exit_status_ready(), str(self.ctrlChannel))
			else:
				print "nope"
			self.connect()
#			print "postconnection"
			if conn:
				if not self.ctrlChannel or self.ctrlChannel.exit_status_ready():
					self.lostConnection()
				else:
					self.ctrlChannel.send('uptime\n')
			

			conn = self.isConnected()
			time.sleep(1)


	def lostConnection(self):
		self.log.warning('Lost connection to %s' % str(self))
		self.log.info ('Stopping all components assigned to this host')

		for comp in self._components:
			comp.lostConnection()

		self.ctrlChannel = None
		self.screenReader = None
		self.ssh.disconnect()
