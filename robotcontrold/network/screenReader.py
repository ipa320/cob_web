import time
from threading import Thread

class ScreenReader(Thread):
	
	def __init__(self, actionName, channel, log):
		Thread.__init__(self)
		self.actionName = actionName
		self.channel = channel
		self.log = log

		self._buffer = 'Idle.'

		self._alive = False


	def isAlive(self):
		return self._alive

	def getBuffer(self):
		return self._buffer


	def start(self):
		if not self._alive:
			self.log.debug('Starting screenReader for action "%s"' % self.actionName)
			self._alive = True
			Thread.start(self)


	
	def run(self):
		try:
			while self._alive:
				if self.channel.recv_ready():
					self.log.debug('ScreenReader received a new line for action "%s"' % self.actionName)
					line = self.channel.recv(1024)
					if not line: break

					self._buffer += line
					if self._buffer.find('[screen is terminating]') > 0:
						self._alive = False
						self.channel.close()


				else:
					time.sleep(2)

		# in case an error occured
		finally:
			self.log.debug('ScreenReader for action "%s" finished' % self.actionName)
			self._alive = False
