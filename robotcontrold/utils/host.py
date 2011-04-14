import time
from threading import Thread
from network.ssh import SSH
from myExceptions.databaseExceptions import CorruptDatabaseError

class Host(Thread):
	
	def __init__(self, rId, hostname, port, user, pw, actions, log):
		Thread.__init__(self)

		self.id = int(rId)
		self.hostname = hostname
		self.port = int(port)
		self.user = user
		self.pw = pw

		self.log = log
		self.ssh = SSH(self)

		self.alive = False

		# any host must have only vncStatus / vncStart / vncStop Action
		if len(actions) != 3 or 'vncStatus' not in actions or 'vncStart' not in actions or 'vncStop' not in actions:
			raise CorruptDatabaseError('Any host requires exactly three actions: vncStatus / vncStart / vncStop')

		self.aVncStatus = actions['vncStatus']
		self.aVncStart  = actions['vncStart']
		self.aVncStop   = actions['vncStop']
		

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


	# Connect / Disconnect are usually not called from outside but from the run method
	def connect(self):
		if not self.isConnected():
			try:
				self.ssh.connect()
				# kill possible old controlScreens
				self.ssh.send('screen -X -S controlScreen kill\n')
				self.ssh.send('screen -S controlScreen\n')
				self.log.info('Connected to %s' % str(self))
			except Exception as e:
				self.log.exception('Could not connect to %s' % str(self))


	def disconnect(self):
		if self.isConnected():
			try:
				try: self.ssh.send('exit\r\n')
				except Exception as e: pass

				self.ssh.disconnect()
				self.log.info('Disconnected from %s' % str(self))
			except Exception as e:
				self.log.exception('Could not disconnect from %s\n' % str(self))
		

	def run(self):
		while self.alive:
			self.connect()
			time.sleep(1)
