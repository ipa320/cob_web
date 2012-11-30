import time, inspect, paramiko
from threading import Thread
from myExceptions.networkExceptions import NoConnectionToHostException


class SSHConnectThread(Thread):
	def __init__(self, sshclient, host):
		Thread.__init__(self)
		self.client = sshclient
		self.host = host

	def run(self):
		self.client.connect(self.host.hostname, self.host.port, self.host.user, self.host.pw, timeout=5)

class SSH():
	def __init__(self, host):
		self.client = paramiko.SSHClient()
		self.client.load_system_host_keys()
		self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		self.host = host
		self.connected = False
		self.channels = []

	def isConnected(self):
		return self.connected


	def connect(self):
		if not self.connected:
			self.client.connect(self.host.hostname, self.host.port, self.host.user, self.host.pw, timeout=2)
			self.connected = True

	def disconnect(self):
		if self.connected:
			# exceptions may be raised, set connected to False as first command
			self.connected = False

			# channels may be already closed, so skip errors
			for channel in self.channels:
				try: channel.close()
				except Exception as e: pass

			self.client.close()

	def exec_command(self, cmd):
		if not self.isConnected():
			raise NoConnectionToHostException('SSH is not connected!')

		return self.client.exec_command(cmd)

	def invokeShell(self):
		if not self.isConnected():
			raise NoConnectionToHostException('SSH is not connected!')

		channel = self.client.invoke_shell()
		self.channels.append(channel)
		return channel


