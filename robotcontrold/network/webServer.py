import threading, time, base64, datetime
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from utils.eventHistory import EventHistory
from myExceptions.webServerExceptions import *


class WebServer(threading.Thread):
	SERVER_AVAILABLE = 1
	SERVER_IN_CHARGE = 2
	SERVER_NOT_AVAILABLE = -1
	
	def __init__(self, serverThread, log, port=8000):
		threading.Thread.__init__(self)

		self.log = log

		self.httpServer = None
		self.serverThread = serverThread
		self.alive = False

		self.log.info ("Creating WebServer on port %d" % port)
		self.httpServer = MyHTTPServer(serverThread, self.log, ('', port), MyHandler)

		self.alive = False


	def __del__(self):
		# stop the server in order to close all open connections. Stop should be normally
		# called anyway. 
		self.stop()


	# @Override 
	def start(self):
		if not self.alive:
			self.log.debug('Starting WebServer')
			self.alive = True
			threading.Thread.start(self)
			
	def checkAccess(self):
		pass;


	def stop(self):
		if self.alive:
			self.log.debug('Stopping WebServer')
			self.alive = False
			self.httpServer.shutdown()


	def isAlive(self):
		return self.alive


	def run(self):
		self.log.debug('Serve forever')
		self.httpServer.serve_forever()
		


class MyHTTPServer(HTTPServer):
	def __init__(self, serverThread, log, opt, handle):
		self.serverThread = serverThread
		HTTPServer.__init__(self, opt, handle)

		self.log = log

		self.protocol_version = 'HTTP/1.1'

		

class MyHandler(BaseHTTPRequestHandler):
	
	def __init__(self, *args):
		BaseHTTPRequestHandler.__init__(self, *args)	


	def do_GET(self):
		serverThread = self.server.serverThread
		activeUser = serverThread.activeUser

		try:
			responseCode = 200
			args = {}
			options = {}
			output = None

			try:
				auth = None
				if self.headers.has_key('Authorization'):
					auth = {'token': str(self.headers['Authorization'])}
					# remove the leading "Basic " before splitting into user/pass
					userPass = base64.b64decode(auth['token'][6:]).split(':')
					if len(userPass) != 2:
						auth = None
						self.server.log.warn('Invalid Authorization Header: %s', str(self.headers['Authorization']))
					else:
						# important: always process names in lowercase
						auth['user'] = userPass[0].lower()
						auth['pass'] = userPass[1]
						if not activeUser:
							auth['status'] = WebServer.SERVER_AVAILABLE
						elif activeUser and activeUser.name == auth['user']:
							auth['status'] = WebServer.SERVER_IN_CHARGE
						else:
							auth['status'] = WebServer.SERVER_NOT_AVAILABLE
				
				# if no auth was sent, return an 401 Unauthorized
				if not auth:
					raise UnauthorizedRequestError('No Auth-Token received', self.path)
					
					
				# get the request user
				requestUser = serverThread.getUserCreateIfNotExistent(auth['user'])
				if not requestUser:
					raise UnauthorizedRequestError('Invalid Auth-Token. No user found.', self.path)
				

				# split the path by the first ?
				argsString, optionsString = self.path.split('?', 1) if self.path.find('?') > 0 else (self.path, '')

				# parse the request (remove the leading and trailing / , then split by /)
				args = argsString.strip('/').split("/")

				# parse the options string
				temp = optionsString.split('&')
				for t in temp:
					key, value = t.split('=',1) if t.find('=') > 0 else (t, '')
					options[key] = value
					
				action = args[0]
				
				
				# Status Command must be available even if no user is logged in
				if action == 'status':
					output = '{"status": %d}' % auth['status']
					
					
				
				# if the action is 'status', just pass, output was created already
				if action == 'status':
					pass
				
				elif action == 'info':
					output  = '[Args]<br>%s<br>' % str(args)
					output += '<br>'
					
					output += '[Options]<br>%s<br>' % str(options)
					output += '<br>'

					output += '[ActiveUser]<br>'
					if activeUser:
						output += 'name:%s<br>' % activeUser.name
					else:
						output += 'None<br>'
					output += '<br>'
					
					output += '[RequestUser]<br>name:%s<br>' % requestUser.name
					output += '<br>'

					output += '[Components]<br>'
					for comp in requestUser.components():
						output += '%s<br>' % str(comp)
					output += '<br>'


					output += '[Hosts]<br>'
					for host in serverThread.hosts.values():
						output += '%s<br>' % str(host)
					output += '<br>'	
					
					output += '[Auth]<br>'
					if not auth:
						output += 'None'
					else:
						output += 'token: %s<br>' % auth['token']
						output += 'user: %s<br>' % auth['user']
						output += 'pass: %s<br>' % auth['pass']
					output += '<br>'
						
							
					
				# Request host / component data
				elif action == 'data':					
					# data/(host|comp)
					if len(args) < 2:
						raise ArgumentRequestError('Wrong argument count for "data". %s found, at least 2 Required.' % str(args), self.path)

					
					if args[1] == 'host':
						hosts = serverThread.hosts
						output = '{'
						for host in hosts.values():
							output += '"%d": {"hostname": "%s", "user": "%s", "port": "%s"},' % (host.id, host.hostname, host.user, host.port)
						# remove the trailing comma
						output = output.strip(',') + '}'
					
					
					elif args[1] == 'comp':						
						output = '{'
						for comp in requestUser.components():
							# first create the actions string for this comp
							actions = '{'
							for action in comp.actions.values():
								# list dependencies
								deps = '['
								for dep in action.dependencies:
									deps += '{"compId": %d, "actionId": %d},' % (dep.component.id, dep.id)
								deps = deps.strip(',') + ']'
								
								# list startCmds
								startCmds = '['
								for cmd in action.startCommands:
									startCmds += '{"id": %d, "command": "%s", "blocking": %s},' % (cmd.id, repr(cmd.command)[1:-1].replace("\"", "\\\""), str(cmd.blocking).lower())
								startCmds = startCmds.strip(',') + ']'
								
								# list stopCmds
								stopCmds = '['
								for cmd in action.stopCommands:
									stopCmds += '{"id": %d, "command": "%s", "blocking": %s},' % (cmd.id, repr(cmd.command)[1:-1].replace("\"", "\\\""), str(cmd.blocking).lower())
								stopCmds = stopCmds.strip(',') + ']'

								
								description = '"' + action.description + '"' if action.description else 'null';
								actions += '\n\t\t"%d": {\n\t\t\t"name": "%s", \n\t\t\t"desc": %s, \n\t\t\t"dependencies":%s, \n\t\t\t"startCmds":%s, \n\t\t\t"stopCmds":%s\n\t\t},' % (action.id, action.name, description, deps, startCmds, stopCmds)
							actions = actions.strip(',') + '\n\t}';
							
							
							# hostId and parentId might be None
							hostId   = '"' + str(comp.host.id)  + '"' if comp.host else 'null'
							parentId = '"' + str(comp.parentId) + '"' if comp.parentId else 'null'
							output += '\n"%d": {\n\t"host": %s, \n\t"name": "%s", \n\t"parentId": %s, \n\t"actions": %s\n},' % (comp.id, hostId, comp.name, parentId, actions)
						# remove the trailing comma
						output = output.strip(',') + '}'
						
					
	
					# Events					
					elif args[1] == 'eventHistory':
						# you must be in charge
						if not auth['status'] == WebServer.SERVER_IN_CHARGE:
							raise UnauthorizedRequestError('You are not in charge.', self.path)
						
						if len(args) != 3:
							raise ArgumentRequestError('Wrong argument count for "data/eventHistory". %s found, 3 Required.' % str(args), self.path)
						
						if not args[2].isdigit():
							raise ArgumentRequestError('Invalid argument for timestamp "%s". timestamp must be numerical.' % args[2], self.path)
							
						timestamp = int(args[2])
						data = EventHistory.getEventData(timestamp)
						
						output = '{"timestamp": "%d", "events": [' % int(time.time())
						for item in data:
							if item['type'] == EventHistory.ACTION_STATUS_EVENT:
								output += '\n\t{"type": "%d", "id": "%d", "comp": "%d", "status": "%d", "ts": "%d"},' % (item['type'], item['id'], item['comp'], item['status'], item['stamp'])
							if item['type'] == EventHistory.HOST_EVENT:
								output += '\n\t{"type": "%d", "id": "%d", "status": "%d", "ts": "%d"},' % (item['type'], item['id'], item['status'], item['stamp'])
						output = output.strip(',') + '\n]}'
						
						
					else:
						raise ArgumentRequestError('Invalid Argument for data "%s". ' % str(args[1]), self.path)
				

				# Start/Stop/Kill/Request status of an action
				elif action == 'exec':
					# you must be in charge
					if not auth['status'] == WebServer.SERVER_IN_CHARGE:
						raise UnauthorizedRequestError('You are not in charge.', self.path)
					
					if len(args) != 4:
						raise ArgumentRequestError('Wrong argument count for "exec". %s found, 4 Required.' % str(args), self.path)

					if not args[1].isdigit():
						raise ArgumentRequestError('Invalid argument for compId "%s". compId must be numerical.' % args[1], self.path)
					if not args[2].isdigit():
						raise ArgumentRequestError('Invalid argument for actionId "%s". actionId must be numerical.' % args[2], self.path)

					compId = int(args[1])
					actionId = int(args[2])
					command = args[3]

					comp = activeUser.get(compId)
					action = comp.getAction(actionId)

					if not comp:
						raise ArgumentRequestError('Component with id "%d" not found' % compId, self.path)

					if not action:
						raise ArgumentRequestError('Action "%d" for component "%d, %s" not found.' % (actionId, compId, comp.name), self.path)


					if command == 'start':
						result = action.start()
					elif command == 'stop':
						result = action.stop()
					elif command == 'kill':
						result = action.kill()
					elif command == 'isAlive':
						result = action.isAlive()
					elif command == 'status':
						result = action.status()
					else:
						raise ArgumentRequestError('Invalid Command "%s".' % command, self.path)

					output = 'OK. Result: %s' % str(result)
			
			
				# Reservations
				elif action == 'reservations':
					if len(args) < 2:
						raise ArgumentRequestError('At least 2 Parameters expected. Received: %s' % str(args), self.path)
						
					if args[1] == 'get':
						output = '{'
						data = serverThread.reservations
						for id in data.keys():
							reservation = data[id]
							if reservation:
								title = '%s %s - %s' % (reservation['user'].name, reservation['start'].strftime('%H:%M'), reservation['end'].strftime('%H:%M'))
								owner = 'true' if reservation['user'] == requestUser else 'false'
								start = reservation['start'].strftime('%Y-%m-%d-%H-%M')
								end = reservation['end'].strftime('%Y-%m-%d-%H-%M')
								output += '"%d": {"title": "%s", "owner": %s, "start": "%s", "end": "%s"},' % (id, title, owner, start, end)
						output = output.strip(',') + '}'
						
						
					elif args[1] == 'add':
						if len(args) != 4:
							raise ArgumentRequestError('4 Parameters expected. Received: %s' % str(args), self.path)
						
					
						# decode start / end date
						try:
							start_date = datetime.datetime.strptime(args[2], "%Y-%m-%d-%H-%M")
							end_date = datetime.datetime.strptime(args[3], "%Y-%m-%d-%H-%M")
						except Exception, e:
							raise ArgumentRequestError('Start-Date or End-Date invalid ["%s", "%s"]' % (args[2], args[3]), self.path)

						#serverThread.addReservation
						output = str(serverThread.addReservation(requestUser, start_date, end_date))
						
						
					elif args[1] == 'extend':
						if len(args) != 4:
							raise ArgumentRequestError('4 Parameters expected. Received: %s' % str(args), self.path)
						
					
						# decode start date
						try:
							end_date = datetime.datetime.strptime(args[3], "%Y-%m-%d-%H-%M")
						except Exception, e:
							raise ArgumentRequestError('End-Date invalid ["%s"]' % args[3], self.path)

						try:
							id = int(args[2])
						except ValueError, e:
							raise ArgumentRequestError('Invalid Reservation id passed', self.path)
							
						try:
							serverThread.extendReservation(id, end_date, requestUser)
						except ValueError,e:
							raise ArgumentRequestError(str(e), self.path)
							
						output = "OK"
						
						
						
					elif args[1] == 'kill':
						if len(args) != 3:
							raise ArgumentRequestError('3 Parameters expected. Received: %s' % str(args), self.path)
						
						try:
							id = int(args[2])
						except ValueError, e:
							raise ArgumentRequestError('Invalid Reservation id passed', self.path)
							
						try:
							serverThread.killReservation(id, requestUser)
						except ValueError,e:
							raise ArgumentRequestError(str(e), self.path)

						output = "OK"
						
						
					else:
						raise ArgumentRequestError('Unexpected reservations argument "%s"' % args[2], self.path)
					

				else:
					raise UnknownRequestError('Unknown request. Args: %s.' % str(args), self.path)
					
				# if output was not set, raise an error	
				if not output:
					raise UnknownRequestError('The request did not produce any output. Args: %s' % str(args), self.path)


			except ArgumentRequestError as e:
				# statusCode 400 Bad Request
				responseCode = 400
				output = '400 %s' % str(e)

			except UnauthorizedRequestError as e:
				# statusCode 401 Unauthorized
				responseCode = 401
				output = '401 %s' % str(e)

			except UnknownRequestError as e:	
				# statusCode 404 Not Found
				responseCode = 404
				output = '404 %s' % str(e)

			except Exception as e:
				# statusCode 500 Internal Server Error
				responseCode = 500
				output = '500 Internal Server Error'
				self.server.log.exception('An error occured parsing the request')


			self.send_response(responseCode)
			self.send_header('Content-Type', 'text/html')
			self.end_headers()
#			self.server.log.debug(output)
#			self.wfile.write(output)#.encode('ascii'))

			if not 'repr' in options:
				self.wfile.write(output.encode('ascii','ignore'))
			else:
				self.wfile.write(repr(output).encode('ascii','ignore'))

		except Exception as e:
			self.server.log.exception('An error occured sending the request')


	# Logging produces too much output
	def log_request(self, code='-', size='-'):
#    	self.server.log.debug('Request: "%s" %s %s' % (self.requestline, str(code), str(size)))
		pass

	def log_error(self, format, *args):
		self.server.log.error(format%args)
	
