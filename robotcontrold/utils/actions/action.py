import time
from utils.eventHistory import EventHistory
from network.screenReader import ScreenReader


class Action():
	def __init__(self, rId, name, _startCommands, _stopCommands, dependencyIds, description, log):
		self.id = int(rId)
		self.name = name
		self.log = log
		
		# dicts with id as key
		self._startCommands = _startCommands
		self._stopCommands = _stopCommands
		
		self.dependencyIds = dependencyIds
		self.description = description;

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
		
	def canStart(self):
		return len(self._startCommands)>0
		
	def canStop(self):
		return len(self._stopCommands)>0

	def screenReaderStopped(self, reader):
		if not self.component:
			raise AttributeError('Component is not set')
			
		if not self.isAlive():
			EventHistory.actionStopped(self, self.component)

	def start(self):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		if not self.isAlive():
			if not self.canStart():
				self.log.info('Cannot start Action "%s", no commands found' % (self.name))
				return
			
			self.log.info('Starting Action "%s". "%d" Commands found' % (self.name, len(self._startCommands)))

			if len(self.dependencies):
				self.log.info('Action depends on: %s' % list('%s>%s' % (item.component.name, item.name) for item in self.dependencies))
				for dep in self.dependencies:
					dep.start()

			for cmd in self._startCommands.values():
				channel = self.component.host.invokeShell()
				self.startChannels.append(channel)

				screenReader = ScreenReader(self.name, channel, self.log, notifyStop=self.screenReaderStopped)
				self.screenReaders.append(screenReader)
				screenReader.start()

				command = self.createScreenCmd(cmd)
				self.log.debug('Running start command "%s" by Action "%s"' % (command.replace('\n','\\n'), self.name))
				channel.send(command)

				# if blocking is enabled for this command, wait for the screenreader to quit
				if cmd.blocking and screenReader and screenReader.isAlive():
					self.log.debug('Command requires blocking. Action "%s" joined the screenReader Thread. Waiting for it to finish' % self.name)
					screenReader.join()


			# notify EventHandler after all cmds run
			if self.isAlive():
				EventHistory.actionRun(self, self.component)

		else:
			self.log.debug('Could not start action "%s", Action still active' % self.name)


	def stop(self, force=False):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		if self.isAlive() or force:
			if not self.canStop():
				self.log.info('Cannot stop Action "%s" (force=%s), no commands found' % (self.name, str(force)))
				return
			
			self.log.info('Stopping Action "%s" (force=%s). "%d" Commands found' % (self.name, str(force), len(self._stopCommands)))

			for cmd in self._stopCommands.values():
				channel = self.component.host.invokeShell()
				command = self.createScreenCmd(cmd)
				self.log.debug('Running stop command "%s" by Action "%s"' % (command.replace('\n','\\n'), self.name))

				screenReader = ScreenReader(self.name, channel, self.log, notifyStop=self.screenReaderStopped)
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
			self.log.info('Killing Action "%s" (force=%s) "%d" Commands found ' % (self.name, str(force), len(self._startCommands)+len(self._stopCommands)))

			# send a break (^C == chr(3)) to every channel
			for channel in self.startChannels:
				channel.send(chr(3))

			# non blocking commands, so only one shell required
			# kill both screens for start and stop command
			channel = self.component.host.invokeShell()
			for cmd in self._startCommands.values()+self._stopCommands.values():
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
 

	def createScreenCmd(self, cmd):
		return 'screen -S %s_%d_%d\n%s\nexit\n' % (self.name, self.id, cmd.id, cmd.command)


	def createKillCmd(self, cmd):
		return 'screen -X -S %s_%d_%d kill\n' % (self.name, self.id, cmd.id)


	def hasCommand(self, cmdId):
		return self.hasStartCommand(cmdId) or self.hasStopCommand(cmdId)
		
	def hasStartCommand(self, cmdId):
		return cmdId in self._startCommands
		
	def hasStopCommand(self, cmdId):
		return cmdId in self._stopCommands
	
	def getCommand(self, cmdId):
		if self.hasStartCommand(cmdId):
			return self._startCommands[cmdId]
		elif self.hasStopCommand(cmdId):
			return self._stopCommands[cmdId]
		else:
			return None
			
	def getStartCommands(self):
		return self._startCommands.values()
	def getStopCommands(self):
		return self._stopCommands.values()
	
	
	def appendDependency(self, action):
		self.dependencies.append(action)
