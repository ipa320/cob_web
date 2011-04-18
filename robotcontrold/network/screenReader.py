import time, re
from threading import Thread

class ScreenReader(Thread):
	
	def __init__(self, name, channel, log):
		Thread.__init__(self)
		self.name = name
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
			self.log.debug('Starting screenReader for "%s"' % self.name)
			self._alive = True
			Thread.start(self)


	
	def run(self):
		regex1 = re.compile('\x1b\[1m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)
		regex2 = re.compile('\x1b\]2;(.*)\x07')
		regex3 = re.compile('\x1b\[31m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)
		regex4 = re.compile('\x00', re.DOTALL)
		regex5 = re.compile('\x1b[^\s\.]*')

		try:
			while self._alive:
				if self.channel.recv_ready():
					self.log.debug('ScreenReader received a new line for "%s"' % self.name)

					line = self.channel.recv(1024)
					if not line: break

					self._buffer += line

					if self._buffer.find('[screen is terminating]') > 0:
						self._alive = False
						self.channel.close()


					self._buffer = re.sub(regex1, '<b>\\1</b>', self._buffer)
					self._buffer = re.sub(regex2, '', self._buffer, re.DOTALL)
					self._buffer = re.sub(regex3, '<font color="red"><b>\\1</b></font>', self._buffer)
					self._buffer = re.sub(regex4, '', self._buffer)
					self._buffer = re.sub(regex5, '', self._buffer)


				else:
					time.sleep(2)

		# in case an error occured
		finally:
			self.log.debug('ScreenReader "%s" finished' % self.name)
			self._alive = False
