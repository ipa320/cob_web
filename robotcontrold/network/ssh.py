import time, inspect
from paramiko import *
from threading import Thread


class SSH():
	def __init__(self, host):
		self.client = SSHClient()
		self.client.load_system_host_keys()
		self.client.set_missing_host_key_policy(AutoAddPolicy())

		self.host = host
		self.connected = False
		self.channel = None

	def isConnected(self):
		return self.connected	


	def connect(self):
		if not self.connected:
			self.client.connect(self.host.hostname, self.host.port, self.host.user, self.host.pw)
			self.channel = self.client.invoke_shell()
			self.connected = True

	def disconnect(self):
		if self.connected:
			# exceptions may be raised, set connected to False as first command
			self.connected = False
			self.channel.close()
			self.client.close()

	#@Override: Make sure the thread cannot be controlled from outside
	def start(self):
		pass


	def send(self, string):
		return self.channel.send(string)

	def recv(self, nbytes):
		return self.channel.recv(nbytes)
