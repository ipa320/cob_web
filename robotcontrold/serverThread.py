import threading
import time


class ServerThread(threading.Thread):
	def __init__(self, log, args):
		threading.Thread.__init__(self)
		self.alive = False

		self.log = log



	# self.stop should be called anyway, but just be be sure
	def __del__(self):
		self.stop()

	
	# @Override 
	def start(self):
		if not self.alive:
			self.alive = True
			threading.Thread.start(self)

	def stop(self):
		if self.alive:
			self.alive = False

	def isAlive(self):
		return self.alive
		
	def run(self):
		while self.alive:
			try:
				print "Running"
				time.sleep(1)
			except Exception,e:
				print "Exception occured: " + str(e)

		
		self.stop()
