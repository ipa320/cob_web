import time
from network.screenReader import ScreenReader


class Action():
	def __init__(self, rId, name, ref_id, start_script, start_args, stop_script, stop_args, log):
		self.id = int(rId)
		self.name = name
		self.ref_id = int(ref_id)
		self.log = log

		# if args are None, set them to '' so we can easily create a string w/o checking args
		self.start_script = start_script
		self.start_args = start_args or ''

		# same: set args '' if not defined
		self.stop_script = stop_script
		self.stop_args = stop_args or ''


		self.host = None
		self.screenReader = None



	def __str__(self):
		return 'Action [id=%d, ref_id=%d, name=%s, script=%s, args=%s]' % (self.id, self.ref_id, self.name, self.script, self.args)


	def setHost(self, host):
		self.host = host

	def isAlive(self):
		return self.screenReader and self.screenReader.isAlive()

	def start(self):
		if not self.host:
			raise AttributeError('Host is not set')
		if not self.isAlive():
			self.log.info('Starting Action "%s"' % self.name)

			# empty the buffer
			self.buffer = ''

			self.log.debug('Opening channel for Action "%s"' % self.name)
			self.channel = self.host.invokeShell()
			self.screenReader = ScreenReader(self.name, self.channel, self.log)
			self.screenReader.start()

			cmd = self.startCmd()
			self.log.debug('Running start command "%s" by Action "%s"' % (cmd.strip(), self.name))
			self.channel.send(cmd)

		else:
			self.log.debug('Could not start action "%s", Action still active' % self.name)


	def stop(self):
		if not self.host:
			raise AttributeError('Host is not set')
		if self.isAlive():
			self.log.info('Stopping Action "%s"' % self.name)

			channel = self.host.invokeShell()
			cmd = self.stopCmd()
			self.log.debug('Running stop command "%s" by Action "%s"' % (cmd.strip(), self.name))
			
			channel.send(cmd)

			# you cannot stop the screenReader. Wait for [screen is terminating] to be received
			# wait for the screenReader to be finished
			if self.screenReader.isAlive():
				self.log.debug('Action "%s" joined the screenReader Thread. Waiting for it to finish' % self.name)
				self.screenReader.join()


	
	def status(self):
		if not self.host:
			raise AttributeError('Host is not set')

		if not self.screenReader:
			return None

		return self.screenReader.getBuffer()


	def startCmd(self):
		return 'screen -L -S %s_%d %s %s\n' % (self.name, self.id, self.start_script, self.start_args)


	def stopCmd(self):
		cmd = ''
		if self.stop_script:
			cmd += 'timeout 10 %s %s && ' % (self.stop_script, self.stop_args)

		cmd += 'screen -X -S %s_%d kill && exit\n' % (self.name, self.id)
		return cmd


