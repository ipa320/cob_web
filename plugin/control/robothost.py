# @package control
# -*- coding: utf8 -*-
#  Module host
#  
#  @author: Regina Klauser
#  @license: BSD License
#

from operation import *
import commands
import sqlite3

import time

def get_hosts( cursor, req, href, processor='control' ):

    hosts = []
    attr_name_list = ['id', 'ip', 'user', 'passwd', 'mac', 'vnc_start', 'vnc_stop', 'port', 'os', 'vncgrep', 'useBgrndServer']
    sql = 'SELECT rowid, ip, user, passwd, mac, vnc_start, vnc_stop, port, os, vncgrep, useBgrndServer FROM robot_hosts'  
        
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
            hosts.append( RobotHost( attributes ))
    except sqlite3.Error, e:
        if processor in 'admin':
            return None
            
    if len(hosts) < 1 and req.perm.has_permission('CONTROL_ADMIN'):
        if processor in 'admin':
            return None
        req.redirect(href + '/admin?operation=new&attr=host&id=')

    return hosts
    
# 
#  Class encapsulates host information 
#
class RobotHost(object):

    def __init__( self, attr_values ):
        self.id = attr_values['id']
        self.ip = attr_values['ip']
        self.user = attr_values['user']
        self.passwd = attr_values['passwd']
        self.mac = attr_values['mac']
        self.os = attr_values['os']
        self.vnc_start = attr_values['vnc_start']
	self.vnc_stop  = attr_values['vnc_stop']
        if attr_values['port'] != None and attr_values['port'] != '':
            self.port = attr_values['port']
        else: 
            self.port = 22
        self.vncgrep = attr_values['vncgrep']
	# useBgrndServer can either be a string (if pulled from mysql) or a boolean (otherwise)
	# convert to a string first and check wheter it matches the string 'true'
	self.useBgrndServer = str(attr_values['useBgrndServer']).lower() == "true"

        self.operations = []
        self.err = ''
        
    def assign_status_operations( self, comp_list ):

        if comp_list == None:
            return
        for comp in comp_list:
            if int(comp.host_id) == int(self.id) and comp.status == 'None':
                cmd = comp.is_active()
                if cmd != '':
                    self.operations.append(Operation( cmd , 'status', comp.title ))

    def create(self, tmp_host):
        
        attr_name_list = ['ip', 'user', 'passwd', 'mac', 'vnc_start', 'vnc_stop', 'port', 'os', 'vncgrep', 'useBgrndServer']
        
        sql = 'INSERT INTO robot_hosts ( '
        i= len(attr_name_list)
        for name in attr_name_list:
            sql += name 
            i = i-1
            if i != 0:
                sql += ', '

        sql += ") VALUES ( '" + tmp_host.ip + "', '" + tmp_host.user + "', '" 
        sql += tmp_host.passwd + "', '" + tmp_host.mac  + "', '" + tmp_host.vnc_start + "', '" + tmp_host.vnc_stop + "', '" 
        sql += str(tmp_host.port) + "', '" + tmp_host.os  + "', '" + tmp_host.vncgrep + "', '"
	sql += str(tmp_host.useBgrndServer) + "')"
             
        return (sql, )

    def update(self, tmp_host):
        
        sql = 'UPDATE robot_hosts SET '
        sql += " user = '" + tmp_host.user +"', passwd = '" + str(tmp_host.passwd) + "', "  
        sql += " mac = '" + tmp_host.mac +"', vnc_start = '" + str(tmp_host.vnc_start) + "', " 
	sql += " vnc_stop = '" + str(tmp_host.vnc_stop) + "', "
        sql += " port = '" + str(tmp_host.port) +"', os = '" + str(tmp_host.os) + "', " 
        sql += " vncgrep = '" + tmp_host.vncgrep  + "', " 
	sql += " useBgrndServer = '" + str(tmp_host.useBgrndServer) + "' "
        sql += "WHERE rowid = '" + self.id + "';"

        return (sql, )
        
    def delete(self):
        sql = "DELETE FROM robot_hosts WHERE rowid = '" + self.id + "';"

        return (sql, )

    def assign_active_operation(self, active_comp, req_attr, req_op ):      
        cmd = ''
        glob_refresh = ''
        quickrefresh = '600' #quichrefresh ist ein STRING! obwohl hier ein Zahlenwert zugeordnet wird.
        if req_attr and req_attr  in 'log':
            cmd = active_comp.tail()
            attr = 'tail_out'
        elif req_op:                
            if req_op in 'start':
                cmd = active_comp.enable()
                attr = 'err'
                glob_refresh = quickrefresh
            elif req_op in 'quit':
                cmd = active_comp.disable()
                attr = 'err'
                glob_refresh = quickrefresh
	    elif req_op in 'restart':
                cmd = active_comp.restart()
                attr = 'err'
                glob_refresh = quickrefresh
            elif req_op in 'wakeonlan':
                self.wakeonlan()
                active_comp.set_err(self.err)
#                glob_refresh = quickrefresh                       
            elif req_op in 'vnc_start' and str(active_comp.display) != '':                
                cmd = active_comp.vnc_start(self.vnc_start)                          
                attr = 'err'                             
                glob_refresh = quickrefresh 
            elif req_op in 'vnc_quit' and str(active_comp.display) != '': 
                cmd = active_comp.vnc_quit(self.vncgrep, self.vnc_stop)
                attr = 'err'
                glob_refresh = quickrefresh 
            else:# req_op in 'refresh':                     
                if str(active_comp.display) != '':
                    cmd = active_comp.get_vnc_status(self.vncgrep) 
                    attr = 'vnc_status'
                if self.os in 'windows':
                    active_comp.check_host(self.ip) 
                    attr = 'windows'
        else:
            if str(active_comp.display) != '':
                cmd = active_comp.get_vnc_status(self.vncgrep) 
                attr = 'vnc_status'
            elif self.os in 'windows':
                active_comp.check_host(self.ip)
        if cmd != '':
            self.operations.append(Operation( cmd, attr, active_comp.title ))
	    
        return glob_refresh
    
    def set_err(self, error):
        self.err = error
        if error in 'unreachable':
            for operation in self.operations:
                operation.set_result('')
                #operation.set_err('Verbindungsversuch zum Host %s ist fehlgeschlagen.'%self.ip)

    def wakeonlan(self):
        err = commands.getoutput( "wakeonlan -i %s -p %s %s" % (self.ip, wakeonlan_port, self.mac ))
        self.set_err(err)
        
