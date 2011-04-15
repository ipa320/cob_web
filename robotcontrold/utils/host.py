import time
from network.ssh import SSH
from myExceptions.databaseExceptions import CorruptDatabaseError

class Host():
	
	def __init__(self, rId, hostname, port, user, pw, actions, log):
		self.id = int(rId)
		self.hostname = hostname
		self.port = int(port)
		self.user = user
		self.pw = pw

		self.log = log

		self.ssh = SSH(self)
		self.ctrlChannel = None

		self.alive = False

		# any host must have only vncStatus / vncStart / vncStop Action
		if len(actions) != 1 or 'vnc' not in actions:
			raise CorruptDatabaseError('Any host requires exactly one action: vnc')

		self.vncAction = actions['vnc']
		self.vncAction.setHost(self)
		

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

	def start(self):
		if not self.alive:
			self.log.debug('Starting %s' % str(self))
			self.alive = True
			Thread.start(self)

	def stop(self):
		if self.alive:
			# put self.alive = False ontop
			self.alive = False			
			self.disconnect()
			self.log.debug('Stopping %s' % str(self))


	def invokeShell(self):
		return self.ssh.invokeShell()

	def exec_command(self, cmd):
		return self.ssh.exec_command(cmd)


	# Connect / Disconnect are usually not called from outside but from the run method
	def connect(self):
		if not self.isConnected():
			try:
				self.ssh.connect()
				self.ctrlChannel = self.invokeShell()

				# kill possible old controlScreens
				self.ctrlChannel.send('screen -X -S controlScreen kill\n')
				self.ctrlChannel.send('screen -S controlScreen\n')
				self.log.info('Connected to %s' % str(self))
			except Exception as e:
				self.log.exception('Could not connect to %s' % str(self))


	def disconnect(self):
		if self.isConnected():
			try:
				try: self.ctrlChannel.send('exit\r\n')
				except Exception as e: pass

				self.ssh.disconnect()
				self.log.info('Disconnected from %s' % str(self))
			except Exception as e:
				self.log.exception('Could not disconnect from %s\n' % str(self))
		
