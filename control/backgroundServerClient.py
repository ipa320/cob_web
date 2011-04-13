
from socket import *
import subprocess
import time


class BackgroundServerClient(object):
	def __init__(self, hosts, port=8081, log=None):
		self.hosts = hosts
		self.port = port
		self.log = log
		self.sock = None
		self.connected = False

	def connectAndRestart(self):
		if not self.connected:
			self.connect()
		self.sock.send('restart\n')		
		self.stopConnection()
				


	def connectAndExecuteCommand(self):
		if not self.connected:
			try:				
				self.connect()
			
			except error,e: # socket.error
				errorStr = ""
				if hasattr(e, 'errno') and e.errno==111:
					errorStr = "Konnte keine Verbindung zum Background-Server aufbauen. "
				else:
					erroStr = "Unerwarteter Fehler beim Verbinden zum Background-Server aufgetreten: " + str(e)

				
				if type(self.hosts)==list:
					hosts = self.hosts
				else:
					hosts = (self.hosts,)

				for host in hosts:
					host.set_err("Host-Error: " + errorStr)
					for op in host.operations:
						op.set_err(errorStr)
				return


		if type(self.hosts)==list:
			hosts = self.hosts
		else:
			hosts = (self.hosts,)

		for host in hosts:
			for op in host.operations:
				self.execOp(host,op)
	

	def connect(self):
		retry = True
		loopNo = 0
		loopTimeout = 5
		while retry:
			loopNo += 1
			retry = False
			try:
				self.sock = socket(AF_INET, SOCK_STREAM)
				self.sock.connect(("localhost", self.port))
				self.sock.send("startsilent\r\n")
				self.sock.send("")
				self.connected = True
			except error,e: # socket.error
				"""# Connection refused, try to start the server if we have not reached the maximum number of retrys:
				if (hasattr(e, 'errno') and e.errno == 111 and loopNo < loopTimeout:
					# Try to start the server
#					subprocess.call(['/home/uhr-ebners/svn/Source/Integration/WebPortal/RoboterZustand/startBgrndServer.sh'])
#					time.sleep(2)
#					retry = True
#					raise Exception("mueste gestartet sein")
					raise e
					
				else:"""
				raise e
		

	def execOp(self, host, operation):
		self.sock.send('exec %s %s' % (host.id, operation.cmd))
		data = self.sock.recv(1024)
		if data[0:1] == "+":
			operation.set_result(data[1:].strip())
		else:
			operation.set_err(data[1:].strip())

	def stopConnection(self):
		if self.connected and self.sock != None:
			self.sock.close()
			self.connected=False
