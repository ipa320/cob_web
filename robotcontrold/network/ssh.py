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
		self.channels = []

	def isConnected(self):
		return self.connected	


	def connect(self):
		if not self.connected:
			self.client.connect(self.host.hostname, self.host.port, self.host.user, self.host.pw)
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

	def invokeShell(self):
		channel = self.client.invoke_shell()
		self.channels.append(channel)
		return channel

