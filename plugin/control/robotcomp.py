## @package comp
# -*- coding: utf8 -*-
#  Module for component management
#  
#  @author: Regina Klauser
#  @license: BSD License
#

#from ssh import *
import os
from twisted.python import log
from operation import *
import sqlite3 
glob = __import__("glob")

import time

def get_comps( cursor, req, hosts, href, log,  processor='control' ):               
    # get the environment-vars
    sql = "SELECT `key`,`value` FROM `robot_env`"
    cursor.execute(sql)
    envVars = cursor.fetchall()

    comps = []
    attr_name_list = ['title', 'search_name', 'host_id', 'start', 'vars', 'log', 'tail_length', 'stop', 'display', 'parent', 'isGroup', 'privilege', 'priority', 'status_cmd']
    sql = 'SELECT '
    i= len(attr_name_list)
    for name in attr_name_list:
        sql += "`" + name + "`"
        i = i-1
        if i != 0:
            sql += ', '
    sql += ' FROM robot_components ORDER BY `priority`, `title`' 
    try:
        cursor.execute( sql )              
        for row in cursor:
            attributes = {}
            i=0
            for value in row:
                if str(value) in 'None':
                    attributes[attr_name_list[i]] = ''
                else:
                    attributes[attr_name_list[i]] = str(value)                    
                i=i+1

            if attributes['isGroup'].lower() == 'true':
            	comps.append(RobotComp(attributes,href))
            else:
            	for host in hosts:
            	    if int(host.id) == int(attributes['host_id']):
#            	        if host.os in 'windows':
#                            comps.append( WindowsComp( attributes, href ))
#            	        elif host.ip in 'localhost':
#                            comps.append( LocalComp( attributes, href ))
#            	        else:
                        comps.append( RemoteComp( attributes, href, envVars ))
        
	if log != None:
		log.debug('number of COMPS: ' + str(len(comps)))

    except sqlite3.Error, e:
        if processor in 'admin':
            return None
        #req.redirect(self.env.href.control() + '/admin?operation=new&attr=comp')
        req.redirect(href + '/admin?operation=new&attr=comp')
    if len(comps) < 1 and req.perm.has_permission('CONTROL_ADMIN'):
        if processor in 'admin':
            return None
        req.redirect(href + '/admin?operation=new&attr=comp')    
          
    return comps

## 
#  Super class for LocalComp and RemoteComp
#                         
class RobotComp(object):       
# The constructor
    #  @param attributes - The attributes of a component
    #  @param global_href - The URL of the module    
    def __init__( self, attr_values, global_href, envVars=None ):       
        self.title = attr_values['title']          
        self.search_name = attr_values['search_name']
        self.host_id = attr_values['host_id']
        self.start = attr_values['start'] 
        self.vars = attr_values['vars']
        self.log = attr_values['log']
        self.tail_length = attr_values['tail_length']
        self.stop = attr_values['stop']
        self.display = attr_values['display']
	self.parent = attr_values['parent']
	self.status_cmd = attr_values['status_cmd']
	self.envVars = envVars

	try:
		self.privilege = int(attr_values['privilege'])
	except ValueError:
		self.privilege = 0

	try:
		self.priority = float(attr_values['priority'])
	except:
		self.priority = 0


	# isGroup can either be a string (if pulled from mysql) or a boolean (otherwise)
	# convert to a string first and check wheter it matches the string 'true'
	self.isGroup = str(attr_values['isGroup']).lower() == 'true'
        
        self.tail_out = ''
        self.err = ''
        self.vnc_status = 'None'
        self.href = global_href + '/' + self.title
        self.status = 'None'

	self.vncbase_port = 8080
    
    def create(self):
        
        attr_name_list = ['title', 'search_name', 'host_id', 'start', 'vars', 'log', 'tail_length', 'stop', 'display', 'parent', 'isGroup', 'privilege', 'priority', 'status_cmd']
        
        sql = 'INSERT INTO robot_components ( '
        i= len(attr_name_list)
        for name in attr_name_list:
            sql += name 
            i = i-1
            if i != 0:
                sql += ', '

        sql += ") VALUES ( '" + self.title + "', '" + self.search_name + "', '" 
        sql += str(self.host_id) + "', '" + self.start + "', '" +self.vars + "', '" 
        sql += self.log + "', '" + self.tail_length + "', '" + self.stop + "', '" 
        sql += self.display + "', '" + self.parent + "', '" + str(self.isGroup) + "', '"
	sql += str(self.privilege) + "', '" + str(self.priority) + "', '" + str(self.status_cmd) + "');"
        return (sql, )
    
    def update(self, tmp_comp):
        
        sql = 'UPDATE robot_components SET '
        sql += " search_name = '" + tmp_comp.search_name +"', host_id = '" + str(tmp_comp.host_id) 
        sql += "', start = '" + tmp_comp.start +"', vars = '" + tmp_comp.vars +"', log = '" + tmp_comp.log 
        sql += "', tail_length = '" + tmp_comp.tail_length + "', stop = '" + tmp_comp.stop
        sql += "', display = '" + tmp_comp.display
	sql += "', parent = '" + tmp_comp.parent
	sql += "', isGroup = '" + str(tmp_comp.isGroup)
	sql += "', priority= '" + str(tmp_comp.priority)
	sql += "', privilege = '" + str(tmp_comp.privilege)
	sql += "', status_cmd = '" + str(tmp_comp.status_cmd)
        sql += "' WHERE title = '" + tmp_comp.title + "';"
		       
        return (sql, )
        
    def delete(self):
        sql = ("UPDATE robot_components SET `parent`='" + self.parent + "' WHERE `parent`='" + self.title + "'", \
	       "DELETE FROM robot_components WHERE title = '" + self.title + "';")
		        
        return sql

# Enable the component process
    def enable(self):
        return ''
    
    
# Disable the component process
    def disable(self):
        return ''
    
     
    
    def restart(self):
        return ''
    
# Set the activity status of a component
    def set_status( self, ignored ):
        return ''
    
    
# Prepare the search name for a grep request
    def prepare(self, grep):
	if self.status_cmd:
		return self.status_cmd
        return '[' + grep[0:1] + "]" + grep[1:] 
    
# Set the status request
    def is_active(self):
        return ''
    
# Set the tail request for the log output
    def tail(self):
        return ''

    def set_err(self, err):
        self.err = err

# Set the status request for the vncserver
    def get_vnc_status(self, vncgrep):
        return ''
    
# Set the port for VNCViewer-URL
    def get_port(self):
        port = int(self.vncbase_port) + int(self.display)
        log.msg(str(port))
        return str(port)
    

    def set_attrs(self, op_attr, op_result, op_err):
        return ''    
    
    def get_display(self):
        return self.display

# Check whether current component is parent to compare
    def contains(self, clist, compare):

	if compare.title == self.title:
		return True

        while compare.parent != '':
            for item in clist:
		if item.title == compare.parent:
			compare = item
			if compare.title == self.title:
				return True;

        return False;

# Check whether this component is parent to any other component
    def hasChilds(self, clist, privilegeLevel):
        for item in clist:
            if item.parent == self.title:
                if not item.isGroup and privilegeLevel >= item.privilege:
	            return True
                if item.hasChilds(clist, privilegeLevel):
	            return True


        return False
	
	
    

    
## 
#  Class for remote components
#
class RemoteComp(RobotComp): 
    
    
# The constructor
    #  @param attributes - The attributes of a component
    #  @param global_href - The URL of the module  
    def __init__(self, attributes, global_href, envVars):	
        RobotComp.__init__( self, attributes, global_href, envVars ) 
#        log.msg('Component %s is on remote host.'%attributes['title'])



    def enable(self):
	logfile = '/dev/null'

	if self.log != '':          
		logfile = self.log 
	else:
		logfile = '/tmp/webportal_log'

	
	cmd = 'echo "Enviroment Variables set by Webportal:" > %s && ' % logfile
	if self.envVars:
		for pair in self.envVars:
			cmd += 'export %s=%s && echo " * %s=%s" >> %s && ' % (pair[0], pair[1], pair[0], pair[1], logfile) 
	if self.display != '':
		cmd += 'export DISPLAY=:%s.0 && echo "* DISPLAY=%s.0" >> %s &&' % (self.display, self.display, logfile)

	cmd += 'echo -e " = = = = = = = = = = = = = = = = = = = = = = = = = = =\\n\\n" >> %s && ' % logfile

        cmd += '( nohup %s %s >> %s 2>&1 )  ' % (self.start, self.vars, logfile)

        return cmd
           
           
# Disable the component process
    #  @return The command for a remote request
    #  @return Ignored 
    def disable(self):
	cmd = ''
	if self.envVars:
		for pair in self.envVars:
			cmd += 'export %s=%s && ' % (pair[0], pair[1]) 

        if self.stop != '':
            cmd = 'nohup ' + self.stop 
            if self.log != '':          
                cmd  += ' > ' + self.log 
            else:
                cmd += ' > /dev/null '
            cmd += ' 2>&1 </dev/null'# &'
        else:
            cmd = 'kill -9 `ps ax | grep "' + self.prepare(self.search_name) + '" | sed -e "s/^ *//;s/ .*//"`'
            
        return cmd


    def restart(self):
        cmd = ''
        if self.stop != '':
            cmd += self.stop
        else:
            cmd += 'kill -9 `ps ax | grep "' + self.prepare(self.search_name) + '" | sed -e "s/^ *//;s/ .*//"`'
        cmd += '&& '
        cmd += 'nohup ' + self.start + ' ' + self.vars
        if self.display != '':
            cmd += ' ' + str(self.display)
        if self.log != '':          
            cmd  += ' > ' + self.log 
        else:
            cmd += ' > /dev/null '
        cmd += ' 2>&1 </dev/null &'
        
        return cmd

# Set the status request
    #  @return The command for a remote request
    #  @return Ignored                
    def is_active(self):
	if self.status_cmd and not self.status_cmd.isspace():
		return self.status_cmd
	 
	if self.log != "":
	        return  'ps ax | grep "' + self.prepare(self.search_name) + '" | grep -v grep | grep -v "' + self.log + '" | sed -e "s/^\s*//;s/\s.*//"'# + '&'
        return  'ps ax | grep "' + self.prepare(self.search_name) + '" | grep -v grep | sed -e "s/^\s*//;s/\s.*//"'# + '&'
    
    
# Set the activity status of a component
    #  @return The command for a remote request
    #  @return Ignored
    def set_status( self, cur_stat ):
        if cur_stat != None:
            self.status = cur_stat
        else:
            self.status = ''
	    log.msg(self.title + ' gets the status '+ self.status )
        return 
     
     
# Set the tail request for the log output 
    #  @return The command for a remote request
    #  @return Ignored       
    def tail(self):
        if self.log != '':    
            cmd = str('ls -l %s | sed -e "s/^-.* 20/20/;" && cat %s | tr -cd "\\11\\12\\40-\\176" | sed -e "s/\[[1-9]*m/<b>/g;s/\[0m/<\/b>/g;s/\]2;-*//"' %(self.log, self.log))
            return cmd
        
# Set the status request for the vncserver
    def get_vnc_status(self, vncgrep):
        if str(self.display) != '':
            cmd = str('ps ax | grep "' + self.prepare(vncgrep) + ' :%s" | sed -e "s/^ *//;s/ .*//"'%str(self.display))
            return cmd
       
        
    
# Start a vncservice
    def vnc_start(self, vnc_path):
        log.msg('vnc_path for display #%s is %s'% (self.display, vnc_path))
        cmd = ''
#        vnc_path = 'Xtightvnc -httpd /usr/share/vnc-java/ -httpport %s  -auth /home/swuser/.Xauthority  -rfbport 8128 -rfbauth /home/swuser/.vnc/passwd '%(self.get_port())
        if str(self.display) != '':
            cmd = 'nohup %s %s '%(str(vnc_path),str(self.display))
            if self.log != '':          
                cmd  += ' > ' + self.log 
            else:
                cmd += ' > /dev/null '
            cmd += ' 2>&1 </dev/null '            
            
        return cmd
        
    
# Stop a vncservice
    def vnc_quit(self, vncgrep, vnc_stop):
        if str(self.display) != '':
            cmd = 'nohup %s %s `ps ax | grep "%s :%s" | sed -e "s/^ *//;s/ .*//"`'   %(str(vnc_stop),str(self.display),self.prepare(vncgrep),str(self.display))
            print "\n\n\nCMD: " + cmd + "\n\n\n"
            if self.log != '':          
                cmd  += ' > ' + self.log 
            else:
                cmd += ' > /dev/null '
            cmd += ' 2>&1 </dev/null '            
            
        return cmd

    def set_attrs(self, op_attr, op_result, op_err):
        log.msg('Setze fuer ' + self.title + ' ' + op_attr + ' auf ' + op_result )
        if op_attr in 'status':
            self.status = op_result
        elif op_attr in 'tail_out':  
            self.tail_out = op_result
        elif op_attr in 'vnc_status':  
            self.vnc_status = op_result
        elif op_attr in 'err': 
            self.err = op_result
        self.err += op_err



