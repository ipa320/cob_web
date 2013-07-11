import threading
import time
import signal

class test(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		print "__init__"
		self.stop = False
		

		signal.signal(signal.SIGINT, self.handler)

	def handler(self,a,b):
		self.stop = True
		print "handler"

	
	def __del__(self):
		print "__del__"

	def __str__(self):
		return "__str__"

	def run(self):
		i=0
		while not self.stop:
			print "yo"
			time.sleep(1)
			i+=1
			if i==5:
				raise Exception("blubb")


if __name__=="__main__":
	test = test()
	test.start()
	print test
	while not test.stop:
		time.sleep(500)
