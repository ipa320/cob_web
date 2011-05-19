# coding: utf-8

import logging
import sys
import time
import sqlite3
import control.robothost
import control.robotcomp
import re
import threading
import socket as socketImport

from bgrndServerCtrlServer import *
from bgrndServerWebServer import *
from bgrndJobs import *


class DummyReq(object):
	def redirect(self, string):
		pass;

class DummyLog(object):
	def debug(self, string):
		pass;
	def log(self, string):
		pass

class ServerThread(threading.Thread):
	# Privilege - Levels
	CONTROL_NONE = 0
	CONTROL_VIEW = 1
	CONTROL_USER = 2
	CONTROL_OPERATOR = 3
	CONTROL_ADMIN = 4

	def __init__(self, trac_path, timeout, log):
		threading.Thread.__init__(self)

		self.trac_path = trac_path
		self.log = log

		self.db = None

		# Timeout for clients
		self.timeout = int(timeout)
		self.lastCommandReceived = 0

		self.syncID = -1

		self.sleeping = False

		self.init()
		self.start()


	def init(self):
		try:
			self.hosts = {}
			self.components = {}

			self.log.info( " * Establishing Mysql Connection")
			self.db =  sqlite3.connect( self.trac_path + "/db/robotcontrol.db",isolation_level=None, check_same_thread = False)
			self.cursor = self.db.cursor()
			self.tracDb =  sqlite3.connect( self.trac_path + "/db/trac.db",isolation_level=None, check_same_thread = False)
			self.tracCursor = self.tracDb.cursor()
		
			self.log.info( " * Loading SyncID")
			self.loadSyncID()

			self.log.info( " * Reading Hosts")
			self.unsortedHosts = control.robothost.get_hosts( self.cursor, DummyReq(), "")


			self.log.info( " * Reading Components")
			self.unsortedComps = control.robotcomp.get_comps( self.cursor, DummyReq(), self.unsortedHosts, "", DummyLog())


			self.log.info( " * Sorting Hosts")
			for host in self.unsortedHosts:
				host.ssh = None
				host.components = []
				host.homeDir = "/home/%s/.bs" % host.user
				self.hosts[host.id] = host


			self.log.info( " * Initializing Components")
			for comp in self.unsortedComps:
				# Every component must be assigned to a valid host. Groups must not.
				if not comp.isGroup and not self.hosts.has_key(comp.host_id):
					self.log.warn( " ! Host with id '%s' not found. Skipping Component '%s'" % (comp.host_id, comp.title))
					continue



				comp.status = 'inactive'
				comp.pidStr = ''
				comp.pids = []
				comp.vncPid = ""
				comp.parentComp = None
				comp.childComps = []
				comp.allChildCompStrings = []
				comp.childCompsString = ""

				self.components[comp.title] = comp


				# Groups dont belong to any host
				if not comp.isGroup:
					comp.host = self.hosts[comp.host_id]
					self.hosts[comp.host_id].components.append(comp)

			self.log.info( " * Sorting Components")
			for comp in self.unsortedComps:
				if comp.parent != None and comp.parent != '':
					if not self.components.has_key(comp.parent):
						raise Exception("Database seems to be corrupt. '%s' parent of '%s' does not exist." % (comp.parent, comp.title))
					parentComp = self.components[comp.parent]
					comp.parentComp = parentComp
					parentComp.childComps.append(comp)


			self.log.info( " * Recursivly Adding all children to component")
			for comp in self.unsortedComps:
				self.recursiveAddAllChildCompStrings(comp)

				comp.childCompsString = '['
				for child in comp.allChildCompStrings:
					comp.childCompsString += '"%s",' % child
				if len(comp.allChildCompStrings) > 0:
					comp.childCompsString = comp.childCompsString[0:-1]
				comp.childCompsString += "]"




			self.log.info( " * Establishing SSH Connections")
			for id,host in self.hosts.iteritems():
				host.ssh = control.ssh.PermanentSSHConnection(host)
				result = self.connectToHost(host)

				if result:
					self.log.info( "  - Host #%s (%s) is UP" % (id, host.ip))
				else:
					self.log.info( "  - Host #%s (%s) is DOWN" % (id, host.ip))



			self.log.info(" * Updating Components' Status")
			self.updateStatus()

			self.log.info( " * Initializing finished. BgrndServer is running !")
			self.active = True



		# if an unexpected error occured during the initialization, stop the server, 
		# so we can close any pending connection and throw the exception afterwards
		except Exception,e: #Debug: ZeroDivisionError instead of Exception
			self.log.critical("Error: " + str(e))
			self.stop()
			raise e



	def __del__(self):
		# stop the server in order to close all open connections. Stop should be normally
		# called anyway. 
		self.stop()


	# This function is called by the webServer to let us know, a user sent a command
	# We might need to reload the user table as its possibly outdated
	def commandReceived(self, args):
		self.lastCommandReceived = time.time()


	def isActive(self):
		return self.active

	def stop(self):
		for id,host in self.hosts.iteritems():
			if not host.ssh == None:
				host.ssh.close()
		if self.db != None:
			self.db.close()

		self.active = False


	def stopComponentsRecursively(self, comp):
		for child in comp.childComps:
			self.stopComponentsRecursively(child)

		self.log.debug('  - Stopping component %s' % comp.title)
		self.getComponentStopJob(comp, None, serverForced=True).execute()

	def stopAllComponents(self):
		self.log.info(' * Stopping all components')

		for comp in self.unsortedComps:
			if not comp.parent:
				self.stopComponentsRecursively(comp)
		self.log.info (' * Stopped all components')



	def run(self):
		elapsed = 0
		while(self.active):
			try:
				if elapsed > 10000:
					elapsed = 0

				if elapsed % 10 == 0:
					if self.loadSyncID():
						self.log.info ( " * SyncID changed. Stopping and reloading data.")
						self.stop()
						self.init()


				if elapsed % 2 == 0:
					lastRequest = time.time() - self.lastCommandReceived
					if lastRequest < self.timeout:
						self.sleeping = False
						self.log.debug(" * Updating components' status; Last request %ds ago; Timeout: %ds" % (int(lastRequest), self.timeout))
						self.updateStatus()
					else:
						if not self.sleeping:
							self.log.info(' * Timeout occured. Shutting down components')
							self.stopAllComponents()
						else:
							self.log.debug(" * Not Updating components' status; Last Request %ds ago; Timeout: %ds" % (int(lastRequest), self.timeout))

						self.sleeping = True


					for id,host in self.hosts.iteritems():
						try:
							# Try to datecheck
							if host.ssh.isConnected():
								data,error = host.ssh.dateCheck()
								if not error:
									self.log.debug ("  - Host #%s (%s) is UP" % (id, host.ip))
								else:
									self.log.debug(" ! KeepAlive: ServerThread pinged host #%s with IP %s, ERR" % (id, host.ip))

							# Try to connected 
							else:
								result = self.connectToHost(host)
								if result:
									self.log.info ("  - Host #%s (%s) is now CONNECTED" % (id, host.ip))
									self.updateStatus()
								else:
									self.log.debug ("  - Host #%s (%s) is still DOWN" % (id, host.ip))

						except Exception,e:
							self.log.error( " ! KeepAlive: ServerThread pinged host #%s with IP %s, Exception %s occured:\n %s" % (id, host.ip, str(type(e)), str(e)))


				# Increment at the end of the loop so that every command will be executed on the first run
				elapsed += 1
				time.sleep(1)

			except Exception,e:
				self.log.error("Exception occured in run(): %s" % str(e))
				

	def recursiveAddAllChildCompStrings(self, baseComp, child=None):
		if child==None:
			child = baseComp

		for comp in child.childComps:
			if not comp.isGroup:
				baseComp.allChildCompStrings.append(comp.title)
			self.recursiveAddAllChildCompStrings(baseComp, comp)


	def loadSyncID(self):
		query = "SELECT `value` FROM `robot_settings` WHERE `key`='SyncID'"
		self.cursor.execute(query)
		newSyncID = self.cursor.fetchone()[0]
		syncIDChanged = newSyncID != self.syncID
		self.syncID = newSyncID

		return syncIDChanged


	def getUser(self, auth):
		if not auth:
			return 'anonymous'
		else:
			sql = "SELECT `name` FROM `robot_auth` WHERE `auth`='%s'" % auth
			self.cursor.execute(sql)
			r = self.cursor.fetchone()
			
			if not r: 
				return 'anonymous'
	
			return r[0]


	def getPrivilegeLevelByAuth(self, auth):
		return self.getPrivilegeLevel(self.getUser(auth))


	def getPrivilegeLevel(self, name):
		# Exclusive Booking Enabled ?
		self.cursor.execute("SELECT COUNT(*) FROM `robot_settings` WHERE `key`='ExclusiveAccess' and `value`='on';")
		bookingEnabled = self.cursor.fetchone()[0] == 1

		serverBooked = False
		if bookingEnabled:
			datetime = time.strftime("%Y-%m-%d %H:%M") 
			sql = "SELECT COUNT(*) FROM `robot_access` WHERE `user`='%s' and `starttime`<='%s' and `endtime`>='%s'" % (name, datetime, datetime)
			serverBooked = self.cursor.execute(sql).fetchone()[0] == 1


		sql = "SELECT `action` FROM `permission` WHERE `username`='%s'" % name
		self.tracCursor.execute(sql)
		r = self.tracCursor.fetchall()
		
		if ('CONTROL_ADMIN',) in r or ('TRAC_ADMIN',) in r:
			maxPrivilegeLevel = self.CONTROL_ADMIN
			privilegeLevel = self.CONTROL_ADMIN
	
		elif ('CONTROL_OPERATOR',) in r:
			maxPrivilegeLevel = self.CONTROL_OPERATOR
			privilegeLevel = maxPrivilegeLevel
			if bookingEnabled and not serverBooked:
				privilegeLevel = self.CONTROL_VIEW
			

		elif ('CONTROL_USER',) in r:
			maxPrivilegeLevel = self.CONTROL_USER
			privilegeLevel = maxPrivilegeLevel
			if bookingEnabled and not serverBooked:
				privilegeLevel = self.CONTROL_VIEW

		elif ('CONTROL_VIEW',) in r:
			maxPrivilegeLevel = self.CONTROL_VIEW
			privilegeLevel = self.CONTROL_VIEW


		else:
			privilegeLevel = self.CONTROL_NONE
			maxPrivilegeLevel = self.CONTROL_NONE


		return {'level': privilegeLevel, 'max': maxPrivilegeLevel}
			


	def execute(self, host_id, cmd):
		if not self.hosts.has_key(host_id):
			return "","Host not found"
		
		host = self.hosts[host_id]
		return host.ssh.execute(cmd)


	def connectToHost(self, host):
		try:
			host.ssh.connect()
		except socketImport.error,e:
			return False

		#print " * Creating Update File"
		host.ssh.execute("mkdir %s" % host.homeDir)
		data, error = host.ssh.execute("echo > %s/status" % host.homeDir)
		if error:
			return False

		for comp in host.components:
			host.ssh.execute("echo \"echo '#'\" >> %s/status" % host.homeDir)
			host.ssh.execute("echo \"%s\" >> %s/status" % (re.sub(r'"','\\"', comp.is_active()), host.homeDir))
		return True


	def getActiveUsers(self):
		if self.tracDb == None or self.tracCursor == None:
			self.tracDb = sqlite3.connect (self.trac_path + "/db/trac.db", isolation_level=None)
			self.tracCursor = self.tracDb.cursor()

		sql = "SELECT COUNT(*) FROM `session_attribute` WHERE `name`='alive' AND CAST(`value` as UNSIGNED)>'%s'" % str(int(time.time() - self.timeout))
		self.activeUsersNum = self.tracCursor.execute(sql).fetchone()[0]


	def updateStatus(self):
		for id, host in self.hosts.iteritems():
			if not host.ssh.isConnected():
				continue


			# Check component status
			try:
				data, error = host.ssh.execute(". %s/status" % host.homeDir)
			except Exception,e:
				error = "Could not update Components status. Assuming host is down. Error: %s" % str(e)
				
			if not error:
				arr = data.split('\n')
				for comp in reversed(host.components):
					if len(arr) == 0:
						break

					next = False
					comp.pids = []

					while not next:
						pid = arr.pop()
						if pid == "#" or len(arr)==0:
							next = True
							continue				

						comp.pids.append(pid)

					comp.pidStr = ", ".join(comp.pids)

					# Check component's vnc status
					# be careful not to set comp.vncPid = "" (because of threading) without checking if it requires vnc at all.
					# If client requests status during checking period the client will see an inactive vnc server.
					# That's because vncPid was unset and the server is still hanging in the ssh period
					if comp.display == "":
						comp.vncPid = ""
					else:
						cmd = comp.get_vnc_status(host.vncgrep)
						vncData, vncError = host.ssh.execute(cmd)
						if not vncError:
							comp.vncPid = vncData.strip()
						else:
							comp.vncPid = ""

			else:
				self.log.warn( " ! Unexpected Exception occured while checking Status. Disconnecting from server: %s" % error)
				host.ssh.disconnect();


	def loadLogfile(self, comp):
#		if not self.components
# CHECK FOR SSH ONLINE
		data, error = comp.host.ssh.execute(comp.tail())
		return comp.log, data, error
	

	def getVncStartJob(self, comp, auth):
		return VncStartJob(comp, auth, self, self.components, self.hosts)


		
	def getVncStopJob(self, comp, auth):
		return VncStopJob(comp, auth, self, self.components, self.hosts)



	def getComponentStartJob(self, comp, auth):
		return ComponentStartJob(comp, auth, self, self.components, self.hosts)


	def getComponentStopJob(self, comp, auth, serverForced=False):
		return ComponentStopJob(comp, auth, self, self.components, self.hosts, serverForced=serverForced)






def main(argv):
	if len(argv) < 6:
		print "Usage: trac_path webPort timeout log_file log_level"
		return

	ctrlServer = None
	try:
		LEVELS = {'debug': logging.DEBUG,
			  'info': logging.INFO,
			  'warning': logging.WARNING,
			  'error': logging.ERROR,
			  'critical': logging.CRITICAL}
		level = LEVELS.get(argv[5], logging.INFO)

		ctrlServer = CtrlServer(argv[1], int(argv[2]), argv[3], argv[4], level)
		response = ctrlServer.cmd_start()

		if ctrlServer.isAlive() and ctrlServer.isServerAlive():
			print " * ControlServer successfully started. Starting Thread."
			ctrlServer.start()
		else:
			print " ! Server are not running. An error must have occured. Shutting down"
			ctrlServer.cmd_shutdown() 
	except Exception,e:
		if ctrlServer:
			ctrlServer.cmd_shutdown()
		print "\n\nAn unexpected Error occured: " + str(e)


port = 8081
if __name__=="__main__":
	main(sys.argv)




