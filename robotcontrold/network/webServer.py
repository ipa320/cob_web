import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


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
		self.serverThread = self.server.serverThread
	


	def do_GET(self):
		try:
			responseCode = 200

			output = ""
			args = self.path.split("/")
			args.remove('')



			output = "Invalid request '%s' %s." % (self.path, str(args))
			responseCode = 404;


			self.send_response(responseCode)
	#		self.send_header('Content-Type', 'text/html')
	#		self.end_headers()
	#		self.server.log.debug(output)
	#		self.wfile.write(output.encode('ascii','ignore'))

		except Exception as e:
			self.server.log.exception('An error occured in do_GET processing the request')


	# 
	def log_request(self, code='-', size='-'):
    		self.server.log.debug('Request: "%s" %s %s' % (self.requestline, str(code), str(size)))

	def log_error(self, format, *args):
		self.server.log.error(format%args)
	
