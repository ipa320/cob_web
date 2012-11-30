#! /usr/bin/env python
import sys
import StringIO
import re
import getopt
import subprocess
import time


# @return StringIO
def buffer_output():
	# buffer stdout into a stringIO
	stdout = sys.stdout
	sys.stdout = StringIO.StringIO()

def reset_buffer_output():
	value = sys.stdout.getvalue()
	sys.stdout = sys.__stdout__
	return value.strip()
	

def get_nodes(package, filename):
	buffer_output()
	roslaunch.main([None, '--nodes', package, filename])
	return reset_buffer_output().split('\n')

def print_nodes(package, filename):
	nodes = get_nodes(package, filename)
	for node in nodes:
		print node

def list_nodes():
	buffer_output()
	rosnode._rosnode_cmd_list([None, 'last'])
	return reset_buffer_output().split('\n')

def print_list_nodes():
	nodes = list_nodes()
	for node in nodes:
		print node

def splitActiveInactiveNodes(package_nodes, running_nodes):
        active = []
        inactive = []
        for current_node in package_nodes:
                if current_node[0:1] != '$':
                        if current_node in running_nodes: 
                                active.append(current_node)
                        else:
                                inactive.append(current_node)

                else:
                        result = re.search('\$\(anon ([a-z_\-]+)\)', current_node)
                        if result:
                                matching_nodes = ', '.join(list(i for i in running_nodes if i.find(result.group(1)) > 0))
                                if matching_nodes:
                                        active.append(matching_nodes)
                                else:
                                        inactive.append(current_node)


	# Workaround
	inactive = list(i for i in inactive if i.find('test') == -1)

        return {'active': active, 'inactive': inactive}


def check_status(package, filename):
	package_nodes = get_nodes(package, filename)
	running_nodes = list_nodes()
	return splitActiveInactiveNodes(package_nodes, running_nodes)


def print_status_verbose(package, filename):
	status = check_status(package, filename)
	print 'Active Nodes:'
	if not len(status['active']):
		print ' > No active nodes'
	for node in status['active']:
		print ' * %s' % node

	print '\nInactive Nodes:'
	if not len(status['inactive']):
		print ' > No inactive nodes'
	for node in status['inactive']:
		print ' * %s' % node


def start_component(package, filename, wait=None, waitForNodes=False, rosrun=False, vgl=False):
	vglPath = '/opt/VirtualGL/bin/vglrun'
	rostype = 'roslaunch'
	if rosrun:
		rostype = 'rosrun'
	

	# load nodes beforehand, this may take a moment
	nodesStillToStart = None
	if waitForNodes:
		nodesStillToStart = get_nodes(package, filename)


	if vgl:
		ps = subprocess.Popen([vglPath, rostype, package, filename])

	else:
		ps = subprocess.Popen([rostype, package, filename])


	if waitForNodes:
		finished = False
		timeout = 400
		cTime = 0
		while cTime < timeout and not finished:
			running_nodes = list_nodes()
			result = splitActiveInactiveNodes(nodesStillToStart, running_nodes)
			nodesStillToStart = result['inactive']
			cTime+=1

			if not len(nodesStillToStart):
				finished = True

			print 'Still to start: ' + str(len(nodesStillToStart))
			print nodesStillToStart
			print
			time.sleep(1)

		if finished:
			print 'Successfullly started nodes'
		
		else:
			print 'Timed out'


	if wait:
		time.sleep(wait)


def print_start_verbose(package, filename, wait=None, waitForNodes=False, rosrun=False, vgl=False):
        print 'Starting \'%s\' from package \'%s\' ' % (filename, package)
	print '= '*30
        print 'Settings: '
        print ' * Vgl: %s' % str(vgl)
        print ' * RosRun: %s' % str(rosrun)
        print ' * Wait: %s' % str(wait)
	print ' * WaitForNodes: %s' % str(waitForNodes)
        print '\n\n'


	print start_component(package, filename, wait=wait, waitForNodes=waitForNodes, rosrun=rosrun, vgl=vgl)

	

def stop_node (node):
	buffer_output()
	rosnode._rosnode_cmd_kill([None, 'kill', node])
	return reset_buffer_output()

def grep_list(grepkill):
	# make sure grepkill contains nothing dangerous
	grepkill = re.sub('[^a-zA-Z_\-]','', grepkill) 

	process = []

	cmd = 'ps ax | grep %s | grep -v grep' % grepkill
	ps = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
	stdout, stderr = ps.communicate()
	lines = stdout.strip().split('\n')
	for line in lines:
		# split off the pid
		info = line.strip().split()
		process.append((info[0], info[4]))
	return process


def kill_process(pid):
	ps = subprocess.Popen(['kill', pid])

	

def print_stop_verbose(package, filename, grepkill=None):
	print 'Node Overview:'
	status = check_status(package, filename)
	print_status_verbose(package, filename)

	running_nodes = status['active']
	if len(running_nodes):
		print '\nStopping %d running Nodes:' % len(running_nodes) 
		for node in running_nodes:
			result = stop_node(node)
			print ' * Killing "%s"' % node
			print '   %s' % node
	else:
		print '\nNo node to stop!'

	if grepkill:
		print '\n\nKilling process with "%s"' % grepkill
		process = grep_list(grepkill)
		for p in process:
			print ' * %s\t: %s' % (p[0], p[1])
			kill_process(p[0])



def main(argv=sys.argv):
	if len(argv) < 2:
		sys.exit('usage: [command]')

	command = argv[1]
	
	if command in ['start', 'get_nodes', 'status', 'status-verbose', 'stop', 'stop-verbose', 'start', 'start-verbose' ] and len(argv) < 4:
		sys.exit ('usage: %s [package] [filename]' % command)



	subprocess.Popen('export ROBOT=cob3-1', shell=True)
	subprocess.Popen('source /opt/ros/cturtle/setup.sh', shell=True)
#source /home/brics/git/care-o-bot/setup.sh /home/brics/git/care-o-bot
#source /home/brics/git/cob3_intern/setup.sh /home/brics/git/cob3_intern
	subprocess.Popen('source /opt/ros/diamondback/setup.bash', shell=True)
	from ros import roslaunch, rosnode


	try:
		if command == 'start':
			package = argv[2]
			filename = argv[3]
			sys.exit(print_list_nodes())
		

		elif command == 'get-nodes':
			package = argv[2]
			filename = argv[3]
			sys.exit(print_nodes(package, filename))


		elif command == 'status-verbose':
			package = argv[2]
			filename = argv[3]
			sys.exit (print_status_verbose(package, filename))

		elif command == 'start-verbose':
			package = argv[2]
			filename = argv[3]
		
			wait = None
			waitForNodes = False
			rosrun = False
			vgl = False
			wait = None
			optlist,args = getopt.getopt(argv[4:], '', ['rosrun', 'vgl', 'wait=', 'waitForNodes'])
			if ('--rosrun','') in optlist:
				rosrun = True
			if ('--waitForNodes','') in optlist:
				waitForNodes = True
			if ('--vgl','') in optlist:
				vgl = True

			waitTime = list(i[1] for i in optlist if i[0] == '--wait')
			if len(waitTime):
				wait = int(waitTime[0])

			sys.exit(print_start_verbose(package, filename, wait=wait, waitForNodes=waitForNodes, rosrun=rosrun, vgl=vgl))

		elif command == 'stop-verbose':
			package = argv[2]
			filename = argv[3]
			
			grepkill=None
			optlist,args = getopt.getopt(argv[4:], '', ['grep-kill='])
			if len(optlist):
				grepkill = optlist[0][1]
			sys.exit(print_stop_verbose(package, filename,grepkill=grepkill))

		elif command == 'list_nodes':
			sys.exit(print_list_nodes())

		else:
			sys.exit('Unknonwn commmand \'%s\'' % command)


	except rosnode.ROSNodeIOException,e:
		sys.exit('ROSNodeIOException: %s' % str(e))

if __name__=='__main__':
	main()
