import sys
from socket import *

def connect(host_id, cmd):
	sock = socket(AF_INET, SOCK_STREAM)
	sock.connect(("localhost", port))
	sock.send('exec %s %s' % (host_id, cmd))
	data = sock.recv(1024)
	sock.close()
	print 'Received', repr(data)

def main(argv):
	if len(argv) < 3:
		print "Usage: host_id cmd"
		return


	host_id = argv[1]
	cmd = argv[2]
	
	connect(host_id, cmd)



port = 8081
if __name__=="__main__":
	main(sys.argv)

