
import logging
import logging.handlers

import threading
import traceback
import sqlite3
from socket import *
from paramiko import AuthenticationException

from bgrndServer import *
from bgrndServerWebServer import *


class CtrlServer(threading.Thread):
	def __init__(self, trac_path, webPort, timeout, logFile, logLevel): 
		threading.Thread.__init__(self)

		self.trac_path = trac_path
		self.webPort = webPort
		self.logFile = logFile
		self.logLevel = logLevel
		self.timeout = int(timeout)
		
		self.serverThread = None
		self.webServer = None

		self.keepAlive = True
		self.keepClient = False
		self.sock = None
		self.conn = None

		self.log = logging.getLogger('CtrlServer')
		self.log.setLevel(self.logLevel)
		self.logHandler = logging.handlers.RotatingFileHandler(self.logFile)
		self.logFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		self.logHandler.setFormatter(self.logFormatter)
		self.log.addHandler(self.logHandler)

	def isAlive(self):
		return self.keepAlive

	def isServerThreadAlive(self):
		return self.serverThread != None and self.serverThread.isActive()

	def isWebServerAlive(self):
		return self.webServer != None and self.webServer.isAlive()

	def isServerAlive(self):
		return self.isServerThreadAlive() and self.isWebServerAlive()

	def cmd_start(self):
		response = ""

		if not self.isServerAlive():
			try:
				logger1 = logging.getLogger('ServerThread')
				logger1.addHandler(self.logHandler)
				logger1.setLevel(self.logLevel)
				logger2 = logging.getLogger('WebServer')
				logger2.addHandler(self.logHandler)
				logger2.setLevel(self.logLevel)

				self.serverThread = ServerThread(self.trac_path, self.timeout, logger1)
				self.webServer = WebServer(self.serverThread, logger2, self.webPort)

				response = "Started Server"
				self.log.info("Created ServerThread + WebServer")

			except sqlite3.OperationalError:
				response = "! Unable to open database"
				self.log.critical("Unable to open database")

				self.cmd_stop()

			except AuthenticationException,e:
				response = "! AuthenticationException occured"
				self.log.critical("AuthenticationException occured: %s" % str(e))
				self.cmd_stop()
	
			except error,e: #socket.error
				if (hasattr(e, 'errno') and e.errno == 113):
					response = "! No route to host"
					self.log.critical("No route to host")
				else:
					response = "! An Socket-Error occured. Stopping Server Thread!\n>> " + str(e)
					self.log.critical("An Socket-Error %s occured while initializing !\n   %s" % (str(type(e)), str(e)))

				self.cmd_stop()

			except Exception,e:
				response = "! An Error occured. Stopping Server Thread!\n>> " + str(type(e))
				self.log.critical("An unexpected Error %s occured while initializing: %s" % (str(type(e)), str(e)))
				traceback.print_exc()

				self.cmd_stop()

		else:
			response = "Server already running"

		return response


	def cmd_stop(self):
		response = ""
		if self.isServerAlive():
			if self.isServerThreadAlive():
				self.serverThread.stop()
				self.serverThread = None

			if self.isWebServerAlive():
				self.webServer.stop()
				self.webServer = None

			response = "Stopping Server"
			self.log.info("Server stopped.")

		else:
			response = "No Server Running"
		return response 


	def cmd_restart(self):
		response   = self.cmd_stop()
		response2  = self.cmd_start()

		response = (response + ' ; ' + response2).strip()
		return response


	def cmd_exec(self, args):
		response = ""
		if len(args) != 2:
			response = "-Wrong argument count"

		elif not self.isServerThreadAlive():
			response = "-Background Server Thread is not running ! Start the server first"
		
		else:
			host_id = args[0]
			cmd = args[1]
			data, error = self.serverThread.execute(host_id, cmd)
			
			if len(error)==0:
				response = "+%s" % data
			else:
				response = "-%s" % error

		return response

	def cmd_close(self, sock, conn):
		response = "Closing Connection"		
		self.log.debug("Closing Connection")

		self.keepClient = False
		return response
 

	def cmd_shutdown(self):
		response = ""

		self.log.info("Shutting down")
		self.cmd_stop()
		self.keepAlive = False
		self.keepClient = False

		if self.isServerThreadAlive():
			self.serverThread.stop()
			self.serverThread = None

		
		return response

	


	def run(self):
		sock = None
		conn = None
		while self.keepAlive:
			try:
				try:
					port = (8000 + self.webPort)
					self.log.info("Staring serverThread on port %d" % port)

					self.sock = socket(AF_INET,SOCK_STREAM)
					self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
					self.sock.bind(("localhost", port))
					self.sock.listen(1)
					self.conn, addr = self.sock.accept()
					self.keepClient = True
				except:
					self.log.critical(" ! Error occured initializing the server. Server already running? Shutting down.")
					self.cmd_shutdown()
					

				# Receive messages
				while self.keepAlive and self.keepClient:
					try:
						time.sleep(0.01)
						data = self.conn.recv(1024)
		
						if not data: break
						else:
							cmds = data.strip().split("\n")
							for cmd in cmds:
								cmd = cmd.strip()
								self.log.debug(" << %s" % cmd)

								response = "Command '" + cmd + "' not understood"

								if cmd == "stop":
									response = self.cmd_stop()
		
								elif cmd == "start":
									response = self.cmd_start()

								elif cmd == "startsilent":
									self.cmd_start()


								elif cmd == "restart":
									response = self.cmd_restart()
																	

								elif cmd == "shutdown":
									response = self.cmd_shutdown()

								elif cmd == "close" or cmd == "exit":
									response = self.cmd_close(sock,conn)

								elif cmd[0:5] == "exec ":
									args = cmd[5:].split(" ",1)
									if (len(args) != 2):
										response = "Usage: exec host_id cmd"

									else:
										response = self.cmd_exec(args)


								if len(response) > 0:
									self.log.debug(" >> %s" % response)
									self.conn.send(str(response) + "\n")

					except Exception,e:
						self.keepClient = False
						self.log.error("Exception occured in run(): %s" % str(e))
						traceback.print_exc()

					finally:
						pass;

			finally:
				self.log.info (" * Closing connection to client")
				if self.conn != None:
					self.conn.close()
				if self.sock != None:
					self.sock.close()
