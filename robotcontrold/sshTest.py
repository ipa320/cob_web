from paramiko import *
import sys

def waitForStart():
	while True:
		line = ch.recv(1000)
		print 'line: ' + line
		if line.endswith('DONE\r\n') and not line.endswith('echo DONE\r\n'):
			print 'START RECEIVED'
			break
		sys.stdin.read(1)

def waitTillDone():
	while True:
		line = ch.recv(1000)
		print 'line: ' + line
		if line.endswith('###\r\n') and not line.endswith('echo ###\r\n')	:
			print 'extra'
			break

def waitForRead():
	read = False
	while not read or ch.recv_ready():
		read = True
		print ch.recv(1000)

def read():
	print ch.recv_ready()
	while(ch.recv_ready()):
		print ch.recv(1000)



def readLine(count, size=1024):
	i=0
	buf = ""
	while i<count:
		line = ch.recv(size);
		buf += line
		i+=1
	return buf


def readAll():
	buf = ""
	while True:
		line = ch.recv(20);
		buf += line
		print line
		if line.strip()[-1:] == '$':
			return buf;

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.connect('cob-sim1', 22, 'webportal', 'rc4')


#i,o,e=ssh.exec_command('echo drin');print e.read();print o.read()
ch = ssh.invoke_shell()
print readLine(2)
print "SENDING ECHO"
ch.send('screen -r\n')
#print readLine(1, size=120)
readAll()


#ch.send('echo HI!!! && echo DONE\n')
#waitForRead()

ssh.close()
