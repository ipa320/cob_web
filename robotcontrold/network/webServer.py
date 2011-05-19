import threading, time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from utils.eventHistory import EventHistory
from myExceptions.webServerExceptions import *


class WebServer(threading.Thread):
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
		user = serverThread.activeUser

		try:
			responseCode = 200
			args = {}
			options = {}
			output = None

			try:
				# if no user is logged in, send a 401 Unauthorized
				if not user:
					raise UnauthorizedRequestError('No User logged in.', self.path)

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
				
				if action == 'info':
					output  = '[Args]<br>%s<br>' % str(args)
					output += '<br>'
					
					output += '[Options]<br>%s<br>' % str(options)
					output += '<br>'

					output += '[User]<br>name:%s<br>' % user.name
					output += '<br>'

					output += '[Components]<br>'
					for comp in user.components():
						output += '%s<br>' % str(comp)
					output += '<br>'


					output += '[Hosts]<br>'
					for host in serverThread.hosts.values():
						output += '%s<br>' % str(host)
						
						
				# Status Command
				elif action == 'status':
					output = 'OK'
							
					
				# Request host / component data
				elif action == 'data':
					# data/(host|comp)
					if len(args) < 2:
						raise ArgumentRequestError('Wrong argument count for "data". %s found, at least 2 Required.' % str(args), self.path)

					if args[1] != 'host' and args[1] != 'comp' and args[1] != 'eventHistory' :
						raise ArgumentRequestError('Argument one must be either "host" or "comp". "%s" found' % str(args[1]), self.path)
					
					
					if args[1] == 'host':
						hosts = serverThread.hosts
						output = '{'
						for host in hosts.values():
							output += '"%d": {"hostname": "%s", "user": "%s", "port": "%s"},' % (host.id, host.hostname, host.user, host.port)
						# remove the trailing comma
						output = output.strip(',') + '}'
					
					
					elif args[1] == 'comp':
						output = '{'
						for comp in user.components():
							# first create the actions string for this comp
							actions = '{'
							for action in comp.actions.values():
								description = '"' + action.description + '"' if action.description else 'null';
								actions += '\n\t\t"%d": {\n\t\t\t"name": "%s", \n\t\t\t"desc": %s, \n\t\t\t"start": ["%s"], \n\t\t\t"stop": ["%s"]\n\t\t},' % (action.id, action.name, description, 'start', 'stop')
							actions = actions.strip(',') + '\n\t}';
							
							
							# hostId and parentId might be None
							hostId   = '"' + str(comp.host.id)  + '"' if comp.host else 'null'
							parentId = '"' + str(comp.parentId) + '"' if comp.parentId else 'null'
							output += '\n"%d": {\n\t"host": %s, \n\t"name": "%s", \n\t"parentId": %s, \n\t"actions": %s\n},' % (comp.id, hostId, comp.name, parentId, actions)
						# remove the trailing comma
						output = output.strip(',') + '}'
						
	
					# Events					
					elif args[1] == 'eventHistory':
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
				

				# Start/Stop/Kill/Request status of an action
				elif action == 'exec':
					if len(args) != 4:
						raise ArgumentRequestError('Wrong argument count for "exec". %s found, 4 Required.' % str(args), self.path)

					if not args[1].isdigit():
						raise ArgumentRequestError('Invalid argument for compId "%s". compId must be numerical.' % args[1], self.path)
					if not args[2].isdigit():
						raise ArgumentRequestError('Invalid argument for actionId "%s". actionId must be numerical.' % args[2], self.path)

					compId = int(args[1])
					actionId = int(args[2])
					command = args[3]

					comp = user.get(compId)
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


	# 
	def log_request(self, code='-', size='-'):
    		self.server.log.debug('Request: "%s" %s %s' % (self.requestline, str(code), str(size)))

	def log_error(self, format, *args):
		self.server.log.error(format%args)
	
