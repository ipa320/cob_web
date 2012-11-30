import time, json
from utils.eventHistory import EventHistory
from network.screenReader import ScreenReader
from utils.actions.shellCommand import ShellCommand


class Action():
	def __init__(self, rId, name, startCommands, stopCommands, description, url, log):
		self.id = int(rId)
		self.name = name
		self.url = url
		self.parameterFile = ''
		self.statusFile = ''
		
		# dicts with id as key
		if not isinstance(startCommands, dict) or not isinstance(stopCommands, dict):
			raise ValueError('Start and Stop Commands must be dicts')
		
		# dicts key id <-> shellCommand
		self._startCommands = startCommands
		self._stopCommands = stopCommands
		
		self.description = description		or ""
		self.dependencies = []

		self.component = None

		
		self.initializeUnpickableData(log)
		
		
	def initializeUnpickableData(self, log):
		if not hasattr(self, '_initialized'):
			self._initialized = True
			self.screenReaders = {'show':[], 'hide':[]}
			self.startChannels = []
			self.stateChannel = None
			self.stateCommand = None
			self.log = log
			self.state = None
			
	
	# used for pickle in memcached. Exclude certain attributes such as log etc
	def __getstate__(self):
		return {
			'id': self.id,
			'name': self.name,
			'url':	self.url,
            'parameterFile': self.parameterFile,
            'statusFile': self.statusFile,
			'_startCommands': self._startCommands,
			'_stopCommands': self._stopCommands,
			'component': self.component,
			'dependencies': self.dependencies,
			'description': self.description
			}


	def getUniqueCommandId(self):
		maxStart = max(self._startCommands.keys()) if len(self._startCommands) > 0 else 0
		maxStop  = max(self._stopCommands.keys())  if len(self._stopCommands) > 0 else 0
		return max(maxStart, maxStop)+1

	def __str__(self):
		return 'Action [id=%d, name=%s, comp=%s]' % (self.id, self.name, self.component if self.component else 'None')


	def setComponent(self, component):
		self.component = component
		
	def isAlive(self):
		for reader in self.screenReaders['show'] + self.screenReaders['hide']:
			if reader and reader.isAlive():
				return True
		return False
	
	def canStart(self):
		return len(self._startCommands)>0
	
	def canStop(self):
		return len(self._stopCommands)>0
	
	def addStartCommand(self, cmd):
		self._startCommands[cmd.id] = cmd
	
	def deleteStartCommand( self, cId ):
		del self._startCommands[ cId ]

	def deleteStopCommand( self, cId ):
		del self._stopCommands[ cId ]

	
	def addStopCommand(self, cmd):
		self._stopCommands[cmd.id] = cmd

	def screenReaderStopped(self, reader):
		if not self.component:
			raise AttributeError('Component is not set')
		
		if not self.isAlive():
			EventHistory.actionStopped(self, self.component)


	# Careful: Function does not check whether readers are alive or dead
	# Once delted, the connection will not be shut down properly
	def clearScreenReaders(self):
		self.screenReaders = {'show': [], 'hide': []}


	def start(self, globalVars=None):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		if not self.isAlive():
			self.clearScreenReaders()

			if not self.canStart():
				self.log.info('Cannot start Action "%s", no commands found' % (self.name))
				return
			
			self.log.info('Starting Action "%s". "%d" Commands / "%d" dependencies found' % (self.name, len(self._startCommands), len(self.dependencies)))

			if len(self.dependencies):
				self.log.info('Action depends on: %s' % list('%s>%s' % (item.component.getName(), item.name) for item in self.dependencies))
				for dep in self.dependencies:
					dep.start()

			for cmd in self._startCommands.values():
				channel = self.component.host.invokeShell()
				command = self.createScreenCmd( cmd, globalVars )
				hideLog = cmd.hideLog
				self.startChannels.append(channel)

				screenReader = ScreenReader(self.name, channel, self.log, notifyStop=self.screenReaderStopped)
				self.screenReaders['hide' if hideLog else 'show'].append(screenReader)
				screenReader.start()

				self.log.debug('Running start command "%s" by Action "%s"' % (command.replace('\n','\\n'), self.name))
				channel.send(command)

				self.constantlyCheckState( globalVars )
				# if blocking is enabled for this command, wait for the screenreader to quit
				if cmd.blocking and screenReader and screenReader.isAlive():
					self.log.debug('Command requires blocking. Action "%s" joined the screenReader Thread. Waiting for it to finish' % self.name)
					screenReader.join( 5.0 )


			# notify EventHandler after all cmds run
			if self.isAlive():
				EventHistory.actionRun(self, self.component)
			
			return True

		else:
			self.log.debug('Could not start action "%s", Action still active' % self.name)
			return False


	def stop(self, force=False, globalVars=None ):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		if self.isAlive() or force:
			self.killStateChannel() 

			if not self.canStop():
				self.log.info('Cannot stop Action "%s" (force=%s), no commands found' % (self.name, str(force)))
				return
			
			self.log.info('Stopping Action "%s" (force=%s). "%d" Commands found' % (self.name, str(force), len(self._stopCommands)))

			for cmd in self._stopCommands.values():
				channel = self.component.host.invokeShell()
				command = self.createScreenCmd( cmd, globalVars )
				hideLog = cmd.hideLog
				
				self.log.debug('Running stop command "%s" by Action "%s"' % (command.replace('\n','\\n'), self.name))

				screenReader = ScreenReader(self.name, channel, self.log, notifyStop=self.screenReaderStopped)
				self.screenReaders['hide' if hideLog else 'show'].append(screenReader)
				screenReader.start()
			
				channel.send(command)

				# if blocking is enabled for this command, wait for the screenreader to quit
				if cmd.blocking and screenReader and screenReader.isAlive():
					self.log.debug('Command requires blocking. Action "%s" joined the screenReader Thread. Waiting for it to finish' % self.name)
					screenReader.join( 5.0 )

			# Wait for all readers (start and stop) to finish
			for reader in self.screenReaders['hide']+self.screenReaders['show']:
				if reader and reader.isAlive():
					self.log.debug('Action "%s"::stop joined the screenReader Thread. Waiting for it to finish' % self.name)
					reader.join( 5.0 )
			print 'IM DONE HERE'


			return True

		else:
			return False

	def constantlyCheckState( self, globalVars=None ):
		if not self.statusFile: 
			return
		loopCmd = 'while true; do %s; sleep 10; done' % self.statusFile
		self.stateCommand = ShellCommand( -1, loopCmd, False, False )
		self.stateChannel = self.component.host.invokeShell()
		command = self.createScreenCmd( self.stateCommand, globalVars )

		self.log.debug('Constantly checking file "%s" for Action "%s"' % (self.statusFile, self.name))

		screenReader = ScreenReader( self.name, self.stateChannel, self.log, 
			notifyNewline=self.notifyNewStatusLine )
		self.screenReaders[ 'show' ].append( screenReader )
		screenReader.start()
	
		self.stateChannel.send(command)

	def notifyNewStatusLine( self, screen, line ):
		configurationStart = line.rfind( '<configuration>' )
		configurationEnd = line.rfind( '</configuration' )
		if configurationStart < 0 or configurationEnd < 0:
			return
		configTxt = line[ configurationStart : configurationEnd ]

		code = ''
		codeStart = configTxt.find( '<code>' )
		codeEnd = configTxt.find( '</code>' )
		if codeStart >= 0 and codeEnd >= 0:
			code = configTxt[ codeStart+len( '<code>' ) : codeEnd ]

		message = ''
		messageStart = configTxt.find( '<message>' )
		messageEnd = configTxt.find( '</message>' )
		if messageStart >= 0 and messageEnd >= 0:
			message = configTxt[ messageStart+len( '<message>' ) : messageEnd ]

		if not self.state or self.state[ 'code' ] != code or self.state[ 'message' ] != message:
			print 'CODE: "%s", MESSGAGE: "%s"' % ( code, message )
			self.state = { 'code': code, 'message': message }
			EventHistory.newState( self, self.component, self.state )

	def forceStop(self):
		return self.stop(force=True)


	def kill(self, force=False):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		if self.isAlive() or force:
			self.killStateChannel() 

			self.log.info('Killing Action "%s" (force=%s) "%d" Commands found ' % (self.name, str(force), len(self._startCommands)+len(self._stopCommands)))

			# send a break (^C == chr(3)) to every channel
			for channel in self.startChannels:
				channel.send(chr(3))
				channel.send( 'exit\n' )


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
			for reader in self.screenReaders['show'] + self.screenReaders['hide']:
				if reader and reader.isAlive():
					self.log.debug('Action "%s"::kill joined the screenReader Thread. Waiting for it to finish' % self.name)
					reader.join( 5.0 )

			return True
		else:
			return False

	def killStateChannel( self ):
		self.log.debug('Killing state channel for Action "%s"' % ( self.name ))
		if self.stateChannel:
			self.stateChannel.send(chr(3))
			self.stateChannel.send( 'exit\n' )

		if self.stateCommand:
			# non blocking commands, so only one shell required
			# kill both screens for start and stop command
			channel = self.component.host.invokeShell()
			cmd = self.createKillCmd( self.stateCommand )
			channel.send(cmd)
		self.state = None
		EventHistory.newState( self, self.component, self.state )

	def forceKill(self):
		return self.kill(force=True)


	def lostConnection(self):
		self.clearScreenReaders()

	
	def status(self):
		if not self.component or not self.component.host:
			raise AttributeError('Host is not set for %s' % str(self))

		text = ''
		for reader in self.screenReaders['show']:
			#			text += 'Name: <b>%s</b><hr />' % reader.name
			text += reader.getBuffer().replace('\r\n', '<br />').replace('\n', '<br />')
			text += '<hr />'

		text = text.strip('<hr />')
		return text if len(text) else 'No data available'
	

	def createScreenCmd(self, cmd, globalVars=None):
		command = 'screen -T dumb -S "%s_%d_%d"\n' % (self.name, self.id, cmd.id )
		if globalVars:
			self.log.debug( 'Setting global variables: %s' % globalVars.keys() )
			for key, value in globalVars.items():
				command += 'export %s="%s"\n' % ( key, value )

		command += '%s\nexit\n' % cmd.command
		return command


	def createKillCmd(self, cmd):
		return 'screen -X -S "%s_%d_%d" kill\n' % (self.name, self.id, cmd.id)


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

	def delteCommand(self, cmdId):
		if self.hasStartCommand(self, cmdId):
			del self._startCommands[cmdId]
		elif self.hasStopCommand(self, cmdId):
			del self._stopCommand[cmdId]
		else:
			raise ValueError('The given cmdId is not part of this action [cmdId="%s", actionId="%s"]' % (cmdId, self.id))
		
			
	def getCommandIds(self):
		return self._startCommands.keys() + self._stopCommands.keys()
			
	def getStartCommands(self):
		return self._startCommands.values()
	def getStopCommands(self):
		return self._stopCommands.values()
	
	
	def appendDependency(self, action):
		if not action in self.dependencies:
			self.dependencies.append(action)

	def deleteDependency(self, action):
		if action in self.dependencies:
			self.dependencies.remove(action)


	def resetDependencies(self):
		self.dependencies = []


	
	# used for webserver
	def createJSONObj(self):
		return {
			'actionId':			self.id,
			'name':				self.name,
			'desc':				self.description,
			'url':				self.url,
            'parameterFile':    self.parameterFile,
            'statusFile':       self.statusFile,
			'dependencies':		list(action.id for action in self.dependencies),
			'startCmds':		list(cmd.createJSONObj() for cmd in self.getStartCommands()),
			'stopCmds':			list(cmd.createJSONObj() for cmd in self.getStopCommands()),
			'state':			self.state
		}
