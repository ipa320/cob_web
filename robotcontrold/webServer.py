import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


class WebServer(threading.Thread):
	def __init__(self, serverThread, log, port=81):
		threading.Thread.__init__(self)

		self.log = log

		self.httpServer = None
		self.serverThread = serverThread
		self.alive = False

		self.log.info ("Creating WebServer on port %d" % port)
		self.httpServer = MyHTTPServer(serverThread, ('', port), MyHandler)

		self.alive = True


	def __del__(self):
		# stop the server in order to close all open connections. Stop should be normally
		# called anyway. 
		self.stop()


	def isAlive(self):
		return self.alive


	def run(self):
		self.log.info( " * Starting WebServer")
		self.httpServer.serve_forever()


	def stop(self):
		if self.alive:
			self.alive = False
			self.httpServer.shutdown()
		


class MyHTTPServer(HTTPServer):
	def __init__(self, serverThread, args0, args1):
		self.serverThread = serverThread
		HTTPServer.__init__(self, args0, args1)

		

class MyHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		output = "Invalid request '%s' %s." % (self.path, str(args))

		self.server.serverThread.log.debug(output)
		self.wfile.write(output.encode('ascii','ignore'))


