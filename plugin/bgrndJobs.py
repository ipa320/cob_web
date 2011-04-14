# coding: utf-8

class JobException(Exception):
	def __init__(self, code, msg):
		self.code = code
		self.msg  = msg.replace('\r\n', ' ').replace('\n', ' ').replace('"', '\\"')

	def __str__(self):
		return "The following Job-Exception occured: Code #%d '%s'" % (self.code, self.msg)


	def ajaxFormat(self):
		return '{"data": {"error":"True", "code": "%d", "errorMsg":"%s"}}' % (self.code, self.msg)


class Job(object):
	def __init__(self, comp, auth, bgrndServer, comps, hosts, serverForced=False):
		self.bgrndServer = bgrndServer
		self.comp = comp
		self.auth = auth
		self.comps = comps
		self.hosts = hosts

		self.name = self.bgrndServer.getUser(self.auth)
		self.priv = self.bgrndServer.getPrivilegeLevel(self.name)['level']

		self.data = {}

		if not serverForced:
			if not self.priv >= self.comp.privilege:
				raise JobException(1, "User '%s' has insufficient rights to start VNC!" % self.name)


	def dataFormat(self):	
		output = '{"data": {'
		
		if len(self.data) > 0:
			for k, v in self.data.iteritems():
				output += '"%s": "%s", ' % (k, v)
			output = output[:-2]

		output += '}}'
		return output




#
# Start a new VNC Server for a certain component
# 
class VncStartJob(Job):
	def __init__(self, comp, auth, bgrndServer, comps, hosts):
		Job.__init__(self, comp, auth, bgrndServer, comps, hosts)


	def execute(self):		
		if self.comp.host.vnc_start.strip() == '':
			raise JobException(2, "No VNC-path defined for corresponding host!")


		# check comp status first
		cmd = self.comp.get_vnc_status(self.comp.host.vncgrep)
		if not cmd or len(cmd.strip()) == 0:
			raise JobException(3, "An error occured while trying to retrieve vnc status. No command specified!")

		data, error = self.comp.host.ssh.execute(cmd)
		if error:
			raise JobException(4, "An error occured while trying to grep vnc status beforehand: '%s'" % error)
		if data:
			self.data = {'error': 'False', 'code': 5, 'msg': "VNC was already running"}
			return

		# if no error occured and its not running yet, start it now
		cmd = self.comp.vnc_start(self.comp.host.vnc_start)
		data, error = self.comp.host.ssh.execute(cmd)
		
		if error:
			raise JobException(6, "Error occured while trying to start VNC: '%s'" % error)


		# check whether it was really started
		cmd = self.comp.get_vnc_status(self.comp.host.vncgrep)
		data, error = self.comp.host.ssh.execute(cmd)
			
		if error:
			raise JobException(7, "VNC started successfully but an error occured while trying to grep vnc status: '%s'" % error)
		if not data:
			raise JobException(8, "VNC Servcer could not be started!")


		# Update the vnc pid right here
		self.comp.vncPid = data.strip()
		self.data = {'error': 'False', 'code': 9, 'msg': 'VNC Server started successfully'}
		return





#
# Start a VNC Server for a certain component
# 
class VncStopJob(Job):
	def __init__(self, comp, auth, bgrndServer, comps, hosts):
		Job.__init__(self, comp, auth, bgrndServer, comps, hosts)

	def execute(self):
		if self.comp.host.vnc_stop.strip() == '':
			raise JobException(2, "No VNC-path defined for corresponding host.")


		# check comp status first
		cmd = self.comp.get_vnc_status(self.comp.host.vncgrep)
		if not cmd or len(cmd.strip()) == 0:
			raise JobException (3, "An error occured while trying to retrieve vnc status. No command specified!")
		data, error = self.comp.host.ssh.execute(cmd)

		if error:
			raise JobException(4, "An error occured while trying to grep vnc status beforehand: '%s'" % error)

		if not data:
			self.data = {'error': 'False', 'code': 5, 'msg': "VNC was not running"}
			return


		# if no error occured and its  running yet, stop it now
		cmd = self.comp.vnc_quit(self.comp.host.vncgrep, self.comp.host.vnc_stop)
		data, error = self.comp.host.ssh.execute(cmd)
				
		if error:
			raise JobException(6, "Error occured while trying to stop VNC: '%s'" % error)


		# check whether it was really stopped
		cmd = self.comp.get_vnc_status(self.comp.host.vncgrep)
		data, error = self.comp.host.ssh.execute(cmd)
					
		if error:
			raise JobException(7, "VNC stopped successfully but an error occured while trying to grep vnc status: '%s'" % error)
		if data:
			raise JobException(8, "VNC service is still running despite killing!")

		self.comp.vncPid = ""
		self.data = {'error': 'False', 'code': 9, 'msg':'VNC Server stopped successfully'}
		return





#
# Start a VNC Server for a certain component
# 
class ComponentStartJob(Job):
	def __init__(self, comp, auth, bgrndServer, comps, hosts):
		Job.__init__(self, comp, auth, bgrndServer, comps, hosts)

	def execute(self):
		# check comp status first
		cmd = self.comp.is_active()
		data, error = self.comp.host.ssh.execute(cmd)

		if error:
			raise JobException(2, "An error occured while trying to grep status beforehand: '%s'" % error)
		if data:
			self.data = {'error': 'False', 'code': 3, 'msg': "Component is already running", 'pid': 'N/A'}
			return


		# if no error occured and its not running yet, start it now
		cmd = self.comp.enable()
		data, error = self.comp.host.ssh.execute(cmd)
		
		if error:
			raise JobException(4, "Error occured while trying to start component: '%s'" % error)


		# check whether it was really started
		cmd = self.comp.is_active()
		data, error = self.comp.host.ssh.execute(cmd)
			
		if error:
			raise JobException(5, "Component appears to have started successfully but an error occured while trying to grep status: '%s'" % error)
		if not data:
			raise JobException(6, "Component could not be started!")

		self.comp.pid = data.strip().replace("\n", ",")
		self.comp.pidStr = self.comp.pid
		self.data = {'error': 'False', 'code': 7, 'msg': 'Component started successfully', 'pid': self.comp.pid}
		return





#
# Start a VNC Server for a certain component
# 
class ComponentStopJob(Job):
	def __init__(self, comp, auth, bgrndServer, comps, hosts, serverForced=False):
		Job.__init__(self, comp, auth, bgrndServer, comps, hosts, serverForced)

	def execute(self):
		# check comp status first
		cmd = self.comp.is_active()
		data, error = self.comp.host.ssh.execute(cmd)

		if error:
			raise JobException (2, "An error occured while trying to grep status beforehand: '%s'" % error)
		if not data:
			self.data = {'error': 'False', 'code': 3, 'msg': "Component is not running"}
			return


		# if no error occured and its not running yet, start it now
		cmd = self.comp.disable()
		data, error = self.comp.host.ssh.execute(cmd)
		
		if error:
			raise JobException (4, "Error occured while trying to stop component: '%s'" % error)


		# check whether it was really started
		cmd = self.comp.is_active()
		data, error = self.comp.host.ssh.execute(cmd)
			
		if error:
			raise JobException (5, "Component stopped successfully but an error occured while trying to grep status: '%s'" % error)
		if data:
			raise JobException (6, "Component could not be closed")

		self.comp.pid = ''
		self.comp.pidStr = ''
		self.data = {'error': 'False', 'code': 7, 'msg': 'Component stopped successfully'}
		return
