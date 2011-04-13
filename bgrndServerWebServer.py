import threading
import traceback
import sqlite3
from socket import *
from paramiko import AuthenticationException
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


from bgrndServer import *
from bgrndJobs import Job, JobException


class WebServer(threading.Thread):
	def __init__(self, serverThread, log, port=81):
		threading.Thread.__init__(self)

		self.log = log

		self.httpServer = None
		self.serverThread = serverThread
		self.alive = False

		self.log.info ("Starting WebServer on port %d" % port)
		self.httpServer = MyHTTPServer(serverThread, ('', port), MyHandler)

		self.alive = True
		self.start()


	def isAlive(self):
		return self.alive

	def run(self):
		self.log.info( " * Starting WebServer")

#		while alive:
#			self.httpServer.handle_request()
		self.httpServer.serve_forever()


	def stop(self):
		self.alive = False
		self.httpServer.shutdown()
		


class MyHTTPServer(HTTPServer):
	def __init__(self, serverThread, args0, args1):
		self.serverThread = serverThread
		HTTPServer.__init__(self, args0, args1)

		

class MyHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		if self.headers.has_key('Authorization'):
			auth = str(self.headers['Authorization'])
		else:
			auth = None

		self.send_response(200)
		self.send_header('Content-Type', 'text/html')
		self.end_headers()

		output = ""
		args = self.path.split("/")
		args.remove('')
		compList = self.server.serverThread.components
		hostList = self.server.serverThread.hosts
		syncID = self.server.serverThread.syncID		


		# Let the serverThread know a command was sent
		self.server.serverThread.commandReceived(args)

		if len(args) == 0:
			output = "No command specified."

		elif args[0] == 'auth':
			output = str(auth)


		elif args[0] == 'pids' and len(args) > 1:
			title = args[1].replace("%20", " ")
			if compList.has_key(title):
				comp = compList[title]
				output = str(comp.pids)

			else:
				output = "Component '%s' not found" % title

		elif args[0] == 'info' and len(args) > 1:
			title = args[1].replace("%20", " ")
			if compList.has_key(title):
				comp = compList[title]
				output = "title: '" + comp.title + "' host_id: '" + str(comp.host_id) + "' "

			else:
				output = "Component '%s' not found" % title

		elif args[0] == 'all':
			for title, comp in compList.iteritems():
				output += comp.title + ": " + str(comp.pids) + "\n"
#			output = str(self.server.serverThread.components.keys())

	
		elif args[0] == 'comp' and len(args) > 1:
			title = args[1].replace("%20", " ")

			if compList.has_key(title):
				comp = compList[title]
				output = str(comp.pids)

			else:
				output = "Component '%s' not found" % title


		elif args[0] == 'basicData':
			name = self.server.serverThread.getUser(auth)
			priv = self.server.serverThread.getPrivilegeLevel(name)['level']

			output = '{"syncID": %s, "name": "%s", "privilege": %d, "data": [{' % (syncID, name, priv)
			for id, host in hostList.iteritems():
				output += '"' + host.id + '":'

				output += '{"ip": "'		+ host.ip	+ '",' \
				       +  ' "port": "'		+ host.port	+ '"' \
				       +  '},'


			output = output[0:-1] + "}, {"


			for title, comp in compList.iteritems():
				output += '"' + comp.title + '":'			

				output += '{"title": "'		+ comp.title		+ '",' \
				       +  ' "privilege": '	+ str(comp.privilege)	+ ' ,' \
				       +  ' "status": "'	+ 'inactive'		+ '",' \
				       +  ' "host_id": "'	+ comp.host_id		+ '",' \
				       +  ' "href": "'		+ ''			+ '",' \
				       +  ' "vnc_status": "'	+ ''			+ '",' \
				       +  ' "stop": "'		+ comp.stop		+ '",' \
				       +  ' "start": "'		+ comp.start		+ '",' \
				       +  ' "vars": "'		+ comp.vars		+ '",' \
				       +  ' "display": "'	+ comp.display		+ '",' \
				       +  ' "vncview_href": "'	+ ''			+ '",' \
				       +  ' "vnc_status": "'	+ ''			+ '",' \
				       +  ' "children": '	+ comp.childCompsString	+ '' \
				       +  '},'


			output = output[0:-1] + "}]}"



		elif args[0] == "updateData":
			output = '{"syncID": %s, "data": [{' % syncID

			for id, host in hostList.iteritems():
				output += '"' + host.id + '": '
				output += '{"on": "'		+ str(host.ssh.isConnected()) + '" ' \
				       +  '},'


			output = output[0:-1] + "}, {"


			for title, comp in compList.iteritems():
				output += '"' + comp.title + '": '
				output += '{"pid": "'	+ comp.pidStr	+ '",' \
				       +  ' "vnc": "'	+ comp.vncPid	+ '"' \
				       +  '},'


			output = output[0:-1] + "}]}"


	
		elif args[0] == "log" and len(args) > 1:
			title = args[1].replace("%20", " ")
			if not compList.has_key(title):
				output = 'Not found\nComponent \'%s\' does not exist.' % title

			else:
				comp = compList[title]
				path, data, error = self.server.serverThread.loadLogfile(comp)
				if not error:
					output = '%s\n%s' % (path, data)

				else:
					output = '%s\nAn error occured reading \'%s\': %s"}}' % (path, path, error)



		elif args[0] == "startVNC" and len(args) > 1:
			title = args[1].replace("%20", " ")

			if not compList.has_key(title):
				output = '{"data": {"error":"True", "errorMsg":"Component could not be found"}}'

			else:
				comp = compList[title]
				job = self.server.serverThread.getVncStartJob(comp, auth)
				try:
					job.execute()
					output = job.dataFormat()
				except JobException, e:
					output = e.ajaxFormat()
				



		elif args[0] == "stopVNC" and len(args) > 1:
			title = args[1].replace("%20", " ")

			if not compList.has_key(title):
				output = '{"data": {"error":"True", "errorMsg":"Component could not be found"}}"'

			else:
				comp = compList[title]
				job = self.server.serverThread.getVncStopJob(comp, auth)
				try:
					job.execute()
					output = job.dataFormat()
				except JobException,e:
					output = e.ajaxFormat()


		elif args[0] == "stop" and len(args) > 1:
			title = args[1].replace("%20", " ")

			if not compList.has_key(title):
				output = '{"data": {"error":"True", "errorMsg":"Component could not be found"}}"'

			else:
				comp = compList[title]
				job = self.server.serverThread.getComponentStopJob(comp,auth)
				try:
					job.execute()
					output = job.dataFormat()
				except JobException,e:
					output = e.ajaxFormat()



		elif args[0] == "start" and len(args) > 1:
			title = args[1].replace("%20", " ")

			if not compList.has_key(title):
				output = '{"data": {"error":"True", "errorMsg":"Component could not be found"}}"'

			else:
				comp = compList[title]
				job = self.server.serverThread.getComponentStartJob(comp,auth)
				try:
					job.execute()
					output = job.dataFormat()
				except JobException,e:
					output = e.ajaxFormat()

		else:
			output = "Invalid request '%s' %s." % (self.path, str(args))


		self.server.serverThread.log.debug(output)
		self.wfile.write(output.encode('ascii','ignore'))
