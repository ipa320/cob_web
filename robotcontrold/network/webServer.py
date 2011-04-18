import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
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

			try:
				# if no user is logged in, send a 401 Unauthorized
				if not user:
					raise UnauthorizedRequestError('Unauthorized access.', self.path)

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


				elif action == 'exec':
					if len(args) != 4:
						raise ArgumentRequestError('Wrong argument count for "exec". %s found, 4 Required.' % str(args), self.path)

					if not args[1].isdigit():
						raise ArgumentRequestError('Invalid argument for compId "%s". compId must be numerical.' % args[1], self.path)

					compId = int(args[1])
					actionName = args[2]
					command = args[3]

					comp = user.getComponent(compId)
					action = comp.get(actionName)

					if not comp:
						raise ArgumentRequestError('Component with id "%d" not found' % compId, self.path)

					if not action:
						raise ArgumentRequestError('Action "%s" for component "%d, %s" not found.' % (actionName, compId, comp.name), self.path)


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


			except ArgumentRequestError as e:
				# statusCode 400 Bad Request
				statusCode = 400
				output = '400 %s' % str(e)

			except UnauthorizedRequestError as e:
				# statusCode 401 Unauthorized
				statusCode = 401
				output = '401 %s' % str(e)

			except UnknownRequestError as e:	
				# statusCode 404 Not Found
				statusCode = 404
				output = '404 %s' % str(e)

			except Exception as e:
				# statusCode 500 Internal Server Error
				statusCode = 500
				output = '500 Internal Server Error'
				self.server.log.exception('An error occured parsing the request')


			self.send_response(responseCode)
			self.send_header('Content-Type', 'text/html')
			self.end_headers()
			self.server.log.debug(output)
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
	
