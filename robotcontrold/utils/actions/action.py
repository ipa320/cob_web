import time
from network.screenReader import ScreenReader


class Action():
	def __init__(self, rId, name, startCommands, stopCommands, dependencyIds, log):
		self.id = int(rId)
		self.name = name
		self.log = log
		self.startCommands = startCommands
		self.stopCommands = stopCommands
		self.dependencyIds = dependencyIds

		self.component = None
		self.screenReaders = []
		self.startChannels = []
		self.dependencies = []



	def __str__(self):
		return 'Action [id=%d, name=%s, comp=%s]' % (self.id, self.name, self.component if self.component else 'None')


	def setComponent(self, component):
		self.component = component

	def isAlive(self):
		for reader in self.screenReaders:
			if reader and reader.isAlive():
				return True
		return False


	def start(self):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		if not self.isAlive():
			self.log.info('Starting Action "%s". "%d" Commands found' % (self.name, len(self.startCommands)))

			if len(self.dependencies):
				self.log.info('Action depends on: %s' % list('%s>%s' % (item.component.name, item.name) for item in self.dependencies))
				for dep in self.dependencies:
					dep.start()

			for cmd in self.startCommands:
				channel = self.component.host.invokeShell()
				self.startChannels.append(channel)

				screenReader = ScreenReader(self.name, channel, self.log)
				self.screenReaders.append(screenReader)
				screenReader.start()

				command = self.createShellCmd(cmd)
				self.log.debug('Running start command "%s" by Action "%s"' % (command.replace('\n','\\n'), self.name))
				channel.send(command)

				# if blocking is enabled for this command, wait for the screenreader to quit
				if cmd.blocking and screenReader and screenReader.isAlive():
					self.log.debug('Command requires blocking. Action "%s" joined the screenReader Thread. Waiting for it to finish' % self.name)
					screenReader.join()


		else:
			self.log.debug('Could not start action "%s", Action still active' % self.name)


	def stop(self, force=False):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		if self.isAlive() or force:
			self.log.info('Stopping Action "%s" (force=%s). "%d" Commands found' % (self.name, str(force), len(self.stopCommands)))

			for cmd in self.stopCommands:
				channel = self.component.host.invokeShell()
				command = self.createShellCmd(cmd)
				self.log.debug('Running stop command "%s" by Action "%s"' % (command.replace('\n','\\n'), self.name))

				screenReader = ScreenReader(self.name, channel, self.log)
				self.screenReaders.append(screenReader)
				screenReader.start()
			
				channel.send(command)

				# if blocking is enabled for this command, wait for the screenreader to quit
				if cmd.blocking and screenReader and screenReader.isAlive():
					self.log.debug('Command requires blocking. Action "%s" joined the screenReader Thread. Waiting for it to finish' % self.name)
					screenReader.join()


			# Wait for all readers (start and stop) to finish
			for reader in self.screenReaders:
				if reader and reader.isAlive():
					self.log.debug('Action "%s"::stop joined the screenReader Thread. Waiting for it to finish' % self.name)
					reader.join()



	def forceStop(self):
		return self.stop(force=True)


	def kill(self, force=False):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		if self.isAlive() or force:
			self.log.info('Killing Action "%s" (force=%s) "%d" Commands found ' % (self.name, str(force), len(self.startCommands)+len(self.stopCommands)))

			# non blocking commands, so only one shell required
			channel = self.component.host.invokeShell()
			for cmd in self.startCommands+self.stopCommands:
				cmd = self.createKillCmd(cmd)
				self.log.debug('Running kill command "%s" by Action "%s"' % (cmd.strip().replace('\n','\\n'), self.name))
				channel.send(cmd)
			
			# send an exit signal
			self.log.debug('Sending exit to close channel.')
			channel.send('exit\n')

			# you cannot stop the screenReader. Wait for [screen is terminating] to be received
			# wait for the screenReader to be finished
			for reader in self.screenReaders:
				if reader and reader.isAlive():
					self.log.debug('Action "%s"::kill joined the screenReader Thread. Waiting for it to finish' % self.name)
					reader.join()


	def forceKill(self):
		return self.kill(force=True)


	def lostConnection(self):
		self.screenReaders = []

	
	def status(self):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		text = 'PRINTING ALL READERS\n------------------------------------\n\n'
		for reader in self.screenReaders:
			text += 'Name: %s\n=============================\n' % reader.name
			text += reader.getBuffer()
		
		return text
 

	def createShellCmd(self, cmd):
		return 'screen -S %s_%d_%d\n%s\nexit\n' % (self.name, self.id, cmd.id, cmd.command)


	def createKillCmd(self, cmd):
		return 'screen -X -S %s_%d_%d kill\n' % (self.name, self.id, cmd.id)

