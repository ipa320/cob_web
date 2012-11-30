from threading import Thread
from paramiko import *
import time, socket, ping

class NetworkTest(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.client = None
		self.connected = False
		self.active = False
		print "* Initialized"

	def start(self):
		self.active = True
		Thread.start(self)
		print "* Started"

	def stop(self):
		print "* Stopping"
		self.active = False

	def run(self):
		print "* Running"
		try:
			while self.active:
				if not self.connected:
					try:
						delay = ping.do_one('cob-sim1', timeout=2)
						print "* Delay: %s" % str(delay)
						self.connect()
					except socket.timeout as e:
						print "* Timed out (connected: %s)" % str(self.connected)
					except Exception as e:
						print "* Error: %s" % str(e)
		

				else:
					try:
						i,o,e = self.client.exec_command("uptime")
						print "O: %s\tE: %s" % (o.read().strip(), e.read().strip())
					except Exception as e:
						print "* Disconnected!"
						self.connected = False
				time.sleep(2)

		finally:
			try: self.client.close()
			except Exception as e:
				print e
		

	def connect(self):
		print "* Connecting"
		self.client = SSHClient()
		self.client.load_system_host_keys()
		self.client.connect("cob-sim1", 22, "webportal", "rc4", timeout=2)
		self.connected = True

	

if __name__=='__main__':
	nt = NetworkTest()
	nt.start()
	try:
		while True:
			time.sleep(5)
	except KeyboardInterrupt as e:
		print " * Keyboard Interrupt"
		nt.stop()
		nt.join()
