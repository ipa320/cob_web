#@package ControlPlugin
# -*- coding: utf8 -*-
#  Trac-plugin for robot process control
#  
#  @author: Regina Klauser
#  @license: BSD License
#

import re

from genshi.builder import tag



from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_script
from trac.web.main import IRequestHandler
from trac.util import escape, Markup
from trac.web.href import Href
from twisted.python import log
from trac.perm import IPermissionRequestor 
import sys, getpass #for ssh-commands
import threading, os, commands, re
import time, datetime

import copy

from ssh import *
from robothost import *
from robotcomp import *
from controladmin import *
from ajaxException import *
from backgroundServerClient import *


#import time
#import traceback




#
#   Trac component class
#
class ControlPlugin(Component):
	implements(INavigationContributor, IRequestHandler, ITemplateProvider, IPermissionRequestor )

	# Privilege - Levels
	CONTROL_NONE = 0
	CONTROL_VIEW = 1
	CONTROL_USER = 2
	CONTROL_OPERATOR = 3
	CONTROL_ADMIN = 4

	# Server - Status
	SERVER_STATUS_AVAILABLE = 1
	SERVER_STATUS_BOOKED = 2
	SERVER_STATUS_UNAVAILABLE = -1
	SERVER_STATUS_UNDEFINED = -2

    
##############Interface-Begin################

	#STATUS: OK
	#IPermissionRequestor method
	#  Return list of permitions privided by this plugin.
	def get_permission_actions(self):
		return ['CONTROL_VIEW', 'CONTROL_ADMIN', 'CONTROL_USER', 'CONTROL_OPERATOR']
        #pass


#----------------next-----------------#


    #INavigationContributor method    
    #  @param req - The request data.
	def get_active_navigation_item(self, req):
		return 'control'

    
    #INavigationContributor method    
    #  @param req - The request data.
	def get_navigation_items(self, req):
		if req.perm.has_permission('CONTROL_VIEW'):   
            #alt
            #yield 'mainnav', 'control', Markup('<a href="%s">Roboterzustand</a>', self.env.href.control())
			#yield ( 'mainnav', 'control', tag.a( 'OezguersRoboterzustand', href=req.href.control() ) )
			yield 'mainnav', 'control', tag.a('RobotControl', href=self.env.href.control())

			
		


#----------------next-----------------#


    #ITemplateProvider method
    #  Return a list of directories containing the provided Genshi templates. 
	def get_templates_dirs(self):
		from pkg_resources import resource_filename
		return [resource_filename(__name__, 'templates')]


    #ITemplateProvider method
    #  Return a list of directories with static resources (such as style sheets, images, etc.)
	def get_htdocs_dirs(self):
		from pkg_resources import resource_filename
		return [('cl', resource_filename(__name__, 'htdocs'))]


#----------------next-----------------#



    #IRequestHandler method
    #  @param req - The request data.
	def match_request(self, req):
		match = re.match('/control(?:/([^/]+))?(?:/([^/]+))?', req.path_info)
		if match:
			req.args['page_id'] = match.group(1)
			self.env.log.info("PAGE_id"+ str(match.group(1)))
			req.args['path_info'] = match.group(2)
			self.env.log.info("PAGE_info"+ str(match.group(2)))
			return True


	def timestamp(self, desc):
		self.env.log.debug("\t##New Timestamp taken: '" + desc + "' time passed: " + str(time.time()-self.zeroTime) + " ms")
		return True

	def openDB(self, db):
		db = sqlite3.connect( self.env.path + db,isolation_level=None)
		cursor = db.cursor()
	
		cursor.execute('CREATE TABLE IF NOT EXISTS "robot_hosts" ("ip" ,"user" ,"passwd" ,"mac" ,"vnc_start", "vnc_stop" ,"port" INTEGER,"os" VARCHAR DEFAULT "linux" , "vncgrep" VARCHAR NOT NULL  DEFAULT "Xtightvnc", "useBgrndServer" BOOL DEFAULT "False")')

		cursor.execute('CREATE TABLE IF NOT EXISTS "robot_components" ("title" VARCHAR PRIMARY KEY  NOT NULL ,"search_name" VARCHAR NOT NULL ,"host_id" INTEGER NOT NULL ,"start" VARCHAR NOT NULL ,"vars" VARCHAR,"log" VARCHAR,"tail_length" INTEGER DEFAULT 15 ,"stop" VARCHAR,"display" INTEGER, "parent" VARCHAR, "isGroup" BOOL, "privilege" INTEGER DEFAULT 0, "priority" INTEGER DEFAULT 0, "status_cmd" VARCHAR)')

		cursor.execute('CREATE TABLE IF NOT EXISTS "robot_access" ("user" VARCHAR,"starttime" DATETIME, "endtime" DATETIME)')

		cursor.execute('CREATE TABLE IF NOT EXISTS "robot_settings" ("key" VARCHAR PRIMARY KEY, "value" VARCHAR)')
		# SyncId must be set
		cursor.execute("SELECT COUNT(*) FROM `robot_settings` WHERE `key`='SyncID'")
		if cursor.fetchone()[0] == 0:
			cursor.execute("INSERT INTO `robot_settings` (`key`,`value`) VALUES ('SyncID',0)")


		cursor.execute('CREATE TABLE IF NOT EXISTS "robot_auth" ("name" VARCHAR , "auth" VARCHAR)')

		cursor.execute('CREATE TABLE IF NOT EXISTS "robot_env" ("options" VARCHAR, "type" VARCHAR, "key" VARCHAR, "value" VARCHAR)')

		db.commit();
		return db, cursor


	def loadServerStatus(self, req, cursor):
		cursor.execute("SELECT COUNT(*) FROM `robot_settings` WHERE `key`='ExclusiveAccess' and `value`='on';")
		self.exclusiveAccessEnabled = cursor.fetchone()[0] == 1

		self.bookingEnds = ""
		self.bookingOwner = ""
		self.bookingExtendable = False
		self.serverStatus = self.SERVER_STATUS_UNDEFINED

		if self.exclusiveAccessEnabled:
			datetime = time.strftime("%Y-%m-%d %H:%M") 
			sql = "SELECT `user`, `endtime` FROM `robot_access` WHERE `starttime`<='%s' and `endtime`>='%s' ORDER BY `endtime` DESC LIMIT 1" % (datetime, datetime)
			cursor.execute(sql)
			result = cursor.fetchone()

			if result == None:
				self.serverStatus = self.SERVER_STATUS_AVAILABLE
			else:
				d = time.strptime(result[1], "%Y-%m-%d %H:%M")
				self.bookingEnds = time.strftime("%H:%M",d)
				self.bookingOwner = result[0]
				
				if result[0] == req.authname:
					self.serverStatus = self.SERVER_STATUS_BOOKED

					# Check whehter the booking is extendable
					sql = "SELECT COUNT(*) FROM `robot_access` WHERE `user`='%s' AND `endtime`>='%s'" % (req.authname, datetime)
					cursor.execute(sql)
					self.bookingExtendable = cursor.fetchone()[0] == 1

				else:
					self.serverStatus = self.SERVER_STATUS_UNAVAILABLE

		else:
			self.serverStatus = self.SERVER_STATUS_BOOKED
		
		

	def loadUserPrivilegeLevel(self, req, cursor, data):
		self.loadServerStatus(req, cursor)

		if req.perm.has_permission('CONTROL_ADMIN'):
			self.privilegeLevel = self.CONTROL_ADMIN
			self.maxPrivilegeLevel = self.CONTROL_ADMIN

		elif req.perm.has_permission('CONTROL_OPERATOR'):
			if self.serverStatus == self.SERVER_STATUS_BOOKED:
				self.privilegeLevel = self.CONTROL_OPERATOR
			else:
				self.privilegeLevel = self.CONTROL_VIEW
			self.maxPrivilegeLevel = self.CONTROL_OPERATOR

		elif req.perm.has_permission('CONTROL_USER'):
			if self.serverStatus == self.SERVER_STATUS_BOOKED:
				self.privilegeLevel = self.CONTROL_USER
			else:
				self.privilegeLevel = self.CONTROL_VIEW
			self.maxPrivilegeLevel = self.CONTROL_USER

		elif req.perm.has_permission('CONTROL_VIEW'):
			self.privilegeLevel = self.CONTROL_VIEW
			self.maxPrivilegeLevel = self.CONTROL_VIEW

		else:
			self.privilegeLevel = self.CONTROL_NONE
			self.maxPrivilegeLevel = self.CONTROL_NONE

		# The data has to be set by this function so we can call loadUserPrivilegeLevel several times
		data['isAdmin'] = self.privilegeLevel >= self.CONTROL_ADMIN
		data['isOperator'] = self.privilegeLevel >= self.CONTROL_OPERATOR
		data['authname'] = req.authname
		data['privilegeLevelString'] = self.privilegeLevelToString(self.privilegeLevel)
		data['exclusiveAccessEnabled'] = self.exclusiveAccessEnabled
		data['serverStatus'] = self.serverStatus
		data['bookingEnds'] = self.bookingEnds
		data['bookingOwner'] = self.bookingOwner
		data['bookingExtendable'] = self.bookingExtendable


		
	def privilegeLevelToString(self, privilegeLevel):
		if privilegeLevel == self.CONTROL_ADMIN:
			return "CONTROL_ADMIN"
		elif privilegeLevel == self.CONTROL_OPERATOR:
			return "CONTROL_OPERATOR"
		elif privilegeLevel == self.CONTROL_USER:
			return "CONTROL_USER"
		elif privilegeLevel == self.CONTROL_VIEW:
			return "CONTROL_VIEW"
		else:
			return "CONTROL_NONE (" + str(privilegeLevel) + ")"

	#IRequestHandler method
	#  @param req - The request data.
	def process_request(self, req):
		#zero the timestamp
		self.zeroTime = time.time()
		self.timestamp("Beginning")
	
		self.env.log.debug("User: " + req.authname)
		

		
		data = {}
		#Die Pfadangabe unter welcher der Apache-Server im lokalen Projekt nach chrome sucht.
		data['trac_chrome_path'] = req.href.chrome()

		
		if req.args.get('advise') != None:
			
			if req.args.get('advise') == 'host':
				data['control_advise'] = "Host"
			else:
				data['control_advise'] = "Component"
			
			return 'control_advise.html', data, None
		
		global refresh
		refresh = ''
 ##       self.refresh = refresh
     



		
		''' Initialize a database for components and message ticker '''
		db, cursor = self.openDB('/db/robotcontrol.db')
		self.loadUserPrivilegeLevel(req, cursor, data)

		# Write the auth string into the database
		auth = req.get_header('Authorization')
		if auth:
			cursor.execute("DELETE FROM `robot_auth` WHERE `name`='%s'" % req.authname)
			cursor.execute("INSERT INTO `robot_auth` (`name`,`auth`) VALUES ('%s','%s')" % (req.authname, auth))
			db.commit()
		
		data['reqBaseUrl'] = req.base_url
		data['uriRoot'] = self.env.href.base
		data['base_url'] = self.env.href.control()
		data['control_admin_page'] = self.env.href.control() + '/admin'

		# admin privileges
		data['hostAdmin'] = self.maxPrivilegeLevel >= self.CONTROL_ADMIN
		data['compAdmin'] = self.maxPrivilegeLevel >= self.CONTROL_OPERATOR
		data['envAdmin']  = self.maxPrivilegeLevel >= self.CONTROL_USER
		


		# Log privilege Level
		self.env.log.debug("PrivilegeLevel: " + str(self.privilegeLevel))


		if not self.maxPrivilegeLevel >= self.CONTROL_VIEW:
			return 'control_permissionDenied.html', {}, None


		#debug
		if req.args.get('page_id') and str(req.args['page_id']) in 'debug':
			response = "req: " + str(dir(req))
			response += "\nget_header('Authorization'): " + str(req.get_header('Authorization'))
			response += "\nget_header('Cookie'): " + str(req.get_header('Cookie'))
			response += "\nbase_url: " + str(req.base_url)
			response += "\n"
			response += "\n" + str(dir(self.env))
			response += "\nbase_url_for_redirect: " + str(self.env.base_url_for_redirect)
			response += "\n" + str(dir(self.env.href))
			response += "\nbase: " + str(self.env.href.base)
			
			response += "\n"
			response += "\nTRAC_ADMIN: " + str(req.perm.has_permission("TRAC_ADMIN"))
			response += "\nCONTROL_ADMIN: " + str(req.perm.has_permission("CONTROL_ADMIN"))
			response += "\nCONTROL_OPERATOR:\t" + str(req.perm.has_permission("CONTROL_OPERATOR"))
			response += "\nCONTROL_USER:\t" + str(req.perm.has_permission("CONTROL_USER"))
			response += "\nCONTROL_VIEW:\t" + str(req.perm.has_permission("CONTROL_VIEW"))


			req.send_response(200)
			req.send_header('Content-Type', 'text/plain')
			req.send_header('Content-Length', (len(response)))

			req.end_headers()

			req.write(response)
			return

		if req.args.get('page_id') and str(req.args['page_id']) in 'template':
			if req.args.get('path_info') and req.args.get('path_info') in 'status':
				active_comp = {'title': 'dT', 'status':'dS', 'host_ip':'dHI', 'host_port':'dHP', 'href':'dHr', 'start':'dSt', 'vars':'dV',
					       'display':'dD', 'vncview_href':'dVV', 'vnc_status':'dVS', 'stop': 'dSto', 'isGroup':False, 'status_cmd': 'dS' }
				buttons = {'op': '', 'vnc_op': ''}

				data['control_active_comp'] = active_comp
				data['control_buttons'] = buttons
				return 'control_status.html', data, None

			if req.args.get('path_info') and req.args.get('path_info') in 'log':
				active_comp = {'log': 'Loading', 'tail_out': 'Loading Log-file, please wait ...'}
				data['control_active_comp'] = active_comp
				return 'control_log.html', data, None



		if req.args.get('page_id') and str(req.args['page_id']) in 'ajax':
			response = 'ready, operation=%s\n' % str(req.args.get('path_info'))
			for k,v in req.args.iteritems():
				response = '%s%s = %s\n' % (response, str(k), str(v))

			sshHAT = None
			try:
				serviceStatus = 0
				debug = req.args.get('debug')!=None

				# Start a selected component
				if req.args.get('path_info') and (req.args.get('path_info') in 'start' or req.args.get('path_info') in 'stop'):
					if debug:
						response = '%s: %s' % (str(req.args.get('path_info')).capitalize(), str(req.args.get('comp')))


					if not req.args.get('comp'):
						raise AjaxException('no comp defined', -1)
	

					#find the active comp
					active_comp_name = req.args.get('comp')
	
					hosts = get_hosts(cursor, req, self.env.href.control())
					if not hosts:
						raise AjaxException('no hosts found',-2)
						
					comps = get_comps(cursor, req, hosts, self.env.href.control(), self.env.log )
					if not comps:
						raise AjaxException('no comps found',-3)

					
					# search for our component
					active_comp = None
					for comp in comps:
						if comp.title == active_comp_name:
							active_comp = comp
							break
					if not active_comp:
						raise AjaxException('active comp not found',-4)

				
					if not self.privilegeLevel >= active_comp.privilege:
						raise AjaxException('permission denied', -6)
	

					
					#search the host for our component
					active_host = None
					for host in hosts:
						if host.id == active_comp.host_id:
							active_host = host
							break
					if not active_host:
						raise AjaxException('active host not found',-5)


					# Create the ssh object
					if active_host.useBgrndServer:
						conn = BackgroundServerClient(host)
					else:
						conn = HostAccessThread(host)

					# Check the status
					host.assign_status_operations((active_comp,))
					host.assign_active_operation(active_comp,'status','vnc_status')
					conn.connectAndExecuteCommand()

					if debug:
						response = '%s\nHost-Error: %s' % (response, str(host.err))
						response = '%s\nOperations: ' % response
						for op in host.operations:
							response = '%s\n- %s' % (response, op)

					
					# Check the result of the status operation
					statusOP = host.operations[0]
					if statusOP.err:
						serviceStatus = -1 # Error occured checking status

					elif statusOP.result: 
						serviceStatus = 1  # Already running

					else:
						serviceStatus = 0  # Not running. Not needed as serviceStatus is not changed,
								   # but to make sure, serviceStatus = 0 if comp not running

					# Check whether vnc is running
					# The component requires a vnc server
					if len(host.operations) > 1:
						vncRunning = host.operations[1].result != ''


					if req.args.get('path_info') in 'start':
						# ServiceStatus = 0 > Not running yet
						# Start the component now!
						if serviceStatus == 0:
							# clear operations list
							host.operations = []

							if active_comp.display != '':
								if not vncRunning:
									host.assign_active_operation(active_comp, 'status', 'vnc_start')
									if debug:
										response += "\nStarting VNC!"
								else:
									if debug:
										response += "\nVNC already running!"
								
							host.assign_active_operation( active_comp, 'start', 'start')
							host.assign_status_operations((active_comp,))
							conn.connectAndExecuteCommand()

							if debug:
								response += '\n'
								response = '%s\nOperations: ' % response
								response = '%s\nHost-Error: %s' % (response, str(host.err))
								for op in host.operations:
									response = '%s\n- %s' % (response, op)

							# Check the result of the start Operation
							statusOP = host.operations[len(host.operations)-1]
							if statusOP.result:
								serviceStatus = 2  # Success 
					
							#elif startOP.result:
							else:
								serviceStatus = -2 # Error occured trying to start service


					if req.args.get('path_info') in 'stop':
						# ServiceStatus = 1 > Component is running
						# Stop the component now!
						if serviceStatus == 1:
							# clear operations list
							host.operations = []
							host.assign_active_operation( active_comp, 'quit', 'quit')
							host.assign_status_operations((active_comp,))
							conn.connectAndExecuteCommand()

							if debug:
								response += '\n'
								response = '%s\nOperations: ' % response
								response = '%s\nHost-Error: %s' % (response, str(host.err))
								for op in host.operations:
									response = '%s\n- %s' % (response, op)

							# Check the result of the start Operation
							statusOP = host.operations[1]
							if statusOP.result:
								serviceStatus = -3  # Error, process still running
					
							#elif startOP.result:
							else:
								serviceStatus = 3 # Success, process died

					
					# Send the result code to the client
					if debug:
						response = '%s\n\nResultCode: %s' % (response, serviceStatus)

					if not debug:
						response = str(serviceStatus)


			except AjaxException,e:
				if debug:
					response = 'error occured: %s (%s)' % e.args
				else:
					response = str(e.args[1])


			try:
				if conn:
					conn.stopConnection()
			except:
				self.env.log.debug("Could not close the ssh connection")

			req.send_response(200)
			req.send_header('Content-Type', 'text/plain')
			req.send_header('Content-Length', (len(response)))
			req.end_headers()

			req.write(response)
			return



		if req.args.get('page_id') and str(req.args['page_id']) in 'admin':            
			## Admin rechte benötigt
			if self.maxPrivilegeLevel < self.CONTROL_OPERATOR or \
			  (req.args.get( 'attr' ) not in ('comp', 'grp') and  self.maxPrivilegeLevel == self.CONTROL_OPERATOR):
				return 'control_permissionDenied.html', {}, None

			## Bemerkung:self.env.href.control ist die alte variante und control_admin hat jetzt einen weiteren Parameter  
			data['control_active_page'] = self.env.href.control()
			
			control_admin(db, req, self.env.href.control(), self.env.log, data )
			
			add_script(req, 'cl/js/control.js')
			add_stylesheet(req, 'cl/css/control.css')    
			add_stylesheet(req, 'cl/css/guestbook.css')
			
			return 'control_admin.html', data, None
		

		self.timestamp("Before the Hosts and Comps are read")		

		''' Hosts and Components '''
		hosts = get_hosts(cursor, req, self.env.href.control())
		comps = get_comps(cursor, req, hosts, self.env.href.control(), self.env.log )

		# if you got here without being redirect you are not admin. Show permission denied sign
		if (not hosts or not comps or len(hosts) == 0 or len(comps) == 0):
			return 'control_permissionDenied.html', {}, None	

		self.timestamp("After the Hosts and Comps are read")



		# ENV-ADMIN
		if req.args.get('page_id') and str(req.args['page_id']) == 'envAdmin':
			if req.args.get('update'):
				s = 'req.args: '
				for k,v in req.args.iteritems():
					k = str(k)
					v = re.sub("[^A-Za-z0-9\._-]", "", str(v))

					# radio values can only be those in options
					sql = "SELECT `type`,`options` FROM `robot_env` WHERE `key`='%s'" % k
					cursor.execute(sql)
					r = cursor.fetchone()
					if r:
						if r[0] == 'radio':
							options = r[1].split(";")
							
						if r[0] != 'radio' or v in options[1::2]:
							sql = "UPDATE `robot_env` SET `value`='%s' WHERE `key`='%s'" % (v, k)
							cursor.execute(sql)
	

				sql = "UPDATE `robot_settings` SET `value`=`value`+1 WHERE `key`='SyncID'"
				cursor.execute(sql)
				db.commit()


			sql = "SELECT `key`, `type`, `value`, `options` FROM `robot_env`"
			cursor.execute(sql)
			r = cursor.fetchall()
			variables = {}
			if r:

				for quadruple in r:
					name    = quadruple[0]
					type    = quadruple[1]
					value   = quadruple[2]
					options = quadruple[3]
					if options:
						options = options.split(";")			
						variables[name] = {'type': type, 'value': value, 'optionKeys': options[1::2], 'optionValues': options[0::2]}
					else:
						variables[name] = {'type': type, 'value': value, 'optionKeys': None, 'optionValues': None}


			data['envVars'] =  variables


			nav_comps = []
			active_comp = None
			for comp in comps:
			    nav_comps.append({'title': comp.title, 
				              'status': comp.status, 
				              'href': comp.href,
				              'parent': comp.parent,
				              'isGroup': comp.isGroup,
				              'priority': comp.priority,
				              'status_cmd': comp.status_cmd})

			# Set a dummy as active component, so no actual component is selected	
			data['control_nav_comps'] = nav_comps
			data['control_active_comp'] = {'title': "", 'parent': "" }

#			data['booking_errors_occured'] = len(errors) > 0
#			data['booking_errors'] = errors
#			data['booking_success'] = success

			add_script(req, 'cl/js/fc.js') #fullcalendar
			add_script(req, 'cl/js/book.js')
			add_stylesheet(req, 'cl/css/fc.css') #fullcalendar
			
			add_script(req, 'cl/js/ajax.js')			 
			add_stylesheet(req, 'cl/css/ajax.css')			 
			add_stylesheet(req, 'cl/css/control.css')    
			add_stylesheet(req, 'cl/css/booking.css')
			add_stylesheet(req, 'cl/css/guestbook.css')
			return 'control_envadmin.html', data, None



		# BOOKING
		if req.args.get('page_id') and str(req.args['page_id']) == 'book':
			if not self.maxPrivilegeLevel >= self.CONTROL_USER:
				return 'control_permissionDenied.html', {}, None 

			errors = []
			success = False
			pi = req.args.get('path_info')
			get_date = None
			dt = time.strftime("%Y-%m-%d %H:%M") 

			sql = None
			try:
				if pi:
					start_date = None
					end_date = None
					start_date_string = None
					end_date_string = None

					if req.args.get('start'):
						start_date = datetime.datetime.strptime(req.args.get('start'), "%Y-%m-%d-%H-%M")
						start_date_string = start_date.strftime("%Y-%m-%d %H:%M")

					if req.args.get('end'):
						end_date = datetime.datetime.strptime(req.args.get('end'), "%Y-%m-%d-%H-%M")
						end_date_string = end_date.strftime("%Y-%m-%d %H:%M")

					compare = datetime.datetime.now() + datetime.timedelta(minutes=-3)

					# Only administrators can create/delete events in the past
					if end_date and end_date < compare:
						errors.append("EndPoint must be set in the future")
					if (end_date and end_date < start_date):
						errors.append('End Date must be set after start Date')
	
			except Exception,e:
				errors.append("Invalid format!")


			if len(errors) == 0:
				if pi == 'book':# and self.serverStatus == self.SERVER_STATUS_AVAILABLE:
					if start_date < compare and not self.privilegeLevel >= self.CONTROL_ADMIN: 
						errors.append("Events in the past cannot be created")

					else:
						sql = "SELECT COUNT(*) FROM `robot_access` WHERE (`starttime`>'%s' AND `starttime`<'%s') OR (`endtime`>'%s' AND `endtime`<'%s') OR (`starttime`<'%s' AND `endtime`>'%s')" % (start_date_string, end_date_string, start_date_string, end_date_string, start_date_string, end_date_string)
						free = cursor.execute(sql).fetchone()[0] == 0
						if (free):
							sql = "INSERT INTO `robot_access` (`user`, `starttime`, `endtime`) VALUES ('%s', '%s', '%s')" % (req.authname, start_date_string, end_date_string)
						else:	
							sql = None
							errors.append("Server is not available at the given date.")


	#			elif pi == 'extend' and self.serverStatus == self.SERVER_STATUS_BOOKED and self.bookingExtendable:
	#				starttime = time.strftime("%Y-%m-%d") + " " + self.bookingEnds
	#				st = datetime.datetime(*time.strptime(starttime, "%Y-%m-%d %H:%M")[:6])
	#				onehour = datetime.timedelta(hours=1)
	#				endtime = (st + onehour).strftime("%Y-%m-%d %H:%M")
	#				sql = "INSERT INTO `robot_access` (`user`, `starttime`, `endtime`) VALUES ('%s', '%s', '%s')" % (req.authname, dt, endtime)

				elif pi == 'extend':
					sql = "SELECT COUNT(*) FROM `robot_access` WHERE `starttime`='%s' AND `user`='%s'" % (start_date_string, req.authname)
					exists = cursor.execute(sql).fetchone()[0] == 1
					if (exists):
						sql = "SELECT COUNT(*) FROM `robot_access` WHERE (`starttime`>'%s' AND `starttime`<'%s')" % (start_date_string, end_date_string)
						free = cursor.execute(sql).fetchone()[0] == 0
						
						if free:
							sql = "UPDATE `robot_access` SET `endtime`='%s' WHERE `starttime`='%s'" % (end_date_string, start_date_string)
						else:
							sql = None
							errors.append('Server is not available at the given time')
					else:
						sql = None
						errors.append("No event to extend. Server is not booked. ")
				

				elif pi == 'kill':# and self.serverStatus == self.SERVER_STATUS_BOOKED:
					if start_date < compare and not self.privilegeLevel >= self.CONTROL_ADMIN: 
						errors.append("Events in the past cannot be deleted")
					else:
						if self.privilegeLevel >= self.CONTROL_ADMIN:
							sql = "SELECT COUNT(*) FROM `robot_access` WHERE `starttime`='%s' AND `endtime`='%s'" % (start_date_string, end_date_string)
						else:
							sql = "SELECT COUNT(*) FROM `robot_access` WHERE `starttime`='%s' AND `endtime`='%s' AND `user`='%s'" % (start_date_string, end_date_string, req.authname)
						exists = cursor.execute(sql).fetchone()[0] == 1
						if (exists):
							sql = "DELETE FROM `robot_access` WHERE `starttime`='%s' AND `endtime`='%s'" % (start_date_string, end_date_string)
						else:
							sql = None
							errors.append("No event to delete. Server is not booked. ")


				elif pi != None and len(pi) > 0:
					errors.append("Unguelige Operation")
			

				if sql != None:
					try:
						cursor.execute(sql)
						db.commit

						# Reload the user privileges 
						self.loadUserPrivilegeLevel(req, cursor, data)
						success = True

					except Exception, e:
#						errors.append("SQL-Error occured")
						errors.append("Query: " + sql + "; SQL-Error: " + str(e))




			# Get all events
			events = []
			sql = "SELECT `user`,`starttime`, `endtime` FROM `robot_access`"
			cursor.execute(sql)
			r = cursor.fetchall()

			if len(r) > 0:
				events = "["
				for row in r:
					date = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M") 
					endTime = datetime.datetime.strptime(row[2], "%Y-%m-%d %H:%M") 
					events += "{title: '%s %d:%d - %d:%d', owner: '%s', allDay: true, " % (row[0], date.hour, date.minute, endTime.hour, endTime.minute, row[0])
					events += "start: new Date(\"%d\", \"%d\", \"%d\", \"%d\", \"%d\"), " % (date.year, date.month-1, date.day, date.hour, date.minute)
					events += "end: new Date(\"%d\",\"%d\",\"%d\", \"%d\", \"%d\") }," %(endTime.year, endTime.month-1, endTime.day, endTime.hour, endTime.minute)
				events = events[:-1] + "]"
			
			# if no event was created, create an empty array
			else:
				events = "[]"

			data['name'] = req.authname
			data['events'] = events

			if not get_date:
				get_date = datetime.date.today()
			data['year'] = get_date.year
			data['month'] = get_date.month-1
			data['day'] = get_date.day



			nav_comps = []
			active_comp = None
			for comp in comps:
			    nav_comps.append({'title': comp.title, 
				              'status': comp.status, 
				              'href': comp.href,
				              'parent': comp.parent,
				              'isGroup': comp.isGroup,
				              'priority': comp.priority,
				              'status_cmd': comp.status_cmd })

			# Set a dummy as active component, so no actual component is selected	
			data['control_nav_comps'] = nav_comps
			data['control_active_comp'] = {'title': "", 'parent': "" }

			data['booking_errors_occured'] = len(errors) > 0
			data['booking_errors'] = errors
			data['booking_success'] = success

			add_script(req, 'cl/js/fc.js') #fullcalendar
			add_script(req, 'cl/js/book.js')
			add_stylesheet(req, 'cl/css/fc.css') #fullcalendar
			
			add_script(req, 'cl/js/ajax.js')			 
			add_stylesheet(req, 'cl/css/ajax.css')			 
			add_stylesheet(req, 'cl/css/control.css')    
			add_stylesheet(req, 'cl/css/booking.css')
			add_stylesheet(req, 'cl/css/guestbook.css')
			return "control_booking.html", data, None


		''' Sort status operations by host '''
		tmp="OPERATIONS\n=======:\n"
		for host in hosts:
		    host.assign_status_operations(comps)    


		''' Active component'''

		active_comp = None
		log.msg('###########ACTIVE_COMP ###########')
		
		#im if teil wird überprüft, ob an der stelle page_id von req_args ein leerer String steht, oder nicht
		if req.args['page_id']:
			
			self.env.log.debug('page_id '+req.args['page_id'])
			log.msg('page_id '+req.args['page_id'])
			for comp in comps:
				self.env.log.debug('comp '+comp.title)
				if comp.title in req.args['page_id'] and len(comp.title) == len(req.args['page_id']) :
					active_comp = comp # shallow copy because of new ActiveOperation object
					self.env.log.debug('active_comp: %s'%active_comp.title)
					log.msg('active_comp: %s'%active_comp.title)


		if active_comp == None:
			active_comp = comps[0]


		data['control_active_page'] = active_comp.href
		data['hasStartPrivilge'] = self.privilegeLevel >= active_comp.privilege
		
		self.env.log.info('active_comp:: %s'%active_comp.title)
		log.msg('active_comp:: %s'%active_comp.title )

		''' Active operation must have operations right '''
		if req.method == 'GET':
			for host in hosts:
				if int(active_comp.host_id) == int(host.id):
					op = req.args.get('operation')
					attr = req.args.get('attr')
					priv = active_comp.privilege

					# status and vnc_status  operations are permitted for everyone, for everything else you need 
					# the privileges
					if str(op) in ('refresh','log','status','vnc_status','None') or self.privilegeLevel >= priv:
						refresh_changed = host.assign_active_operation( active_comp, attr, op)
						self.env.log.debug("Assigning operation '"+str(op)+"',attr: '"+ str(attr) + "' to comp:'" + active_comp.title + "')")
						if refresh_changed != '':
							refresh = refresh_changed
					else:
						self.env.log.debug("Operation '" + str(op) + "' not permitted for user '" + str(req.authname) + "' on component '" + active_comp.title + "'")

		
	
		self.timestamp("Before the SSH Commands are executed")
		
		# SSH Connection 
		sshHosts = []
		bgrndServerHosts = []

		for host in hosts:
			self.env.log.debug('useBgrndServer: ' + str(host.useBgrndServer) + "; " + str(host.useBgrndServer == True))
			if host.useBgrndServer == True:
				bgrndServerHosts.append(host)
			else:
				sshHosts.append(host)

		if len(sshHosts) > 0:
			sshConnectionForHosts = SSHAccess(sshHosts,log=self.env.log)
			sshConnectionForHosts.startConnection()

		if len(bgrndServerHosts) > 0:
			bgrndClient = BackgroundServerClient(bgrndServerHosts,log=self.env.log)
			bgrndClient.connectAndExecuteCommand()
			bgrndClient.stopConnection()

		self.env.log.debug('sshHosts: ' + str(len(sshHosts)) + '; bgrndServerHosts: ' + str(len(bgrndServerHosts)))
		
		
		self.env.log.debug('Thread execution accomplished')
		self.timestamp("After the SSH Commands are executed")

		for host in hosts:
		    for op in host.operations:
		        for comp in comps:
		            if op.comp_title in comp.title and len(op.comp_title) == len(comp.title):
		                comp.set_attrs(op.attr, op.result, op.err)




		self.env.log.debug('----------------------------------- ')
		self.env.log.debug('####################################')

		''' ********** LOGGING ********** '''
		self.env.log.debug('---------- comp in comps --------- ')
		for comp in comps:
		    self.env.log.debug( comp.title + ' hat den Status ' + comp.status )
		    if comp.display != '':
		        self.env.log.debug( 'VNCStatus fuer Display %s ist %s'%(str(comp.display), comp.vnc_status ))
		for host in hosts:
		    self.env.log.debug( 'OPERATIONS for ' + host.ip ) 
		    for op in host.operations:
		        self.env.log.debug( str(op) )
		
		''' ****************************** ''' 

		''' control.html'''
		data['control_refresh'] = refresh
		data['control_active_attr'] = 'status'
		
		if req.args.get( 'attr' ) and str(req.args.get( 'attr' )) != '':
			data['control_active_attr'] = req.args.get( 'attr' )
			
		''' control_nav.html'''
		nav_comps = []
		for comp in comps:
		    nav_comps.append({'title': comp.title, 
		                      'status': comp.status, 
		                      'href': comp.href,
		                      'parent': comp.parent,
		                      'isGroup': comp.isGroup,
		                      'priority': comp.priority,
		                      'status_cmd': comp.status_cmd})
		self.env.log.debug(nav_comps)	

		data['control_nav_comps'] = nav_comps
		
		nav_attrs = []
		nav_attrs.append({'id': 'status', 'Name': 'Status', 'Href': 'operation=refresh&attr=status'})

		if active_comp.log != '':
		    nav_attrs.append({'id': 'log', 'Name': 'Logs', 'Href': 'operation=refresh&attr=log'})

		if active_comp.status != '' and self.privilegeLevel >= active_comp.privilege:
		    nav_attrs.append({'id': 'restart', 'Name': 'Restart', 'Href': 'operation=restart&attr=status'})

		if not active_comp.isGroup:
			data['control_attributes'] = nav_attrs
		else:
			data['control_attributes'] = []
		
		
		''' Buttons '''
		data['control_buttons'] = self.get_button_labels(req, active_comp )
		''' control_status.htmland control_log.cs'''
		active_host = None      
		for host in hosts:
		    if int(active_comp.host_id) == int(host.id):
		        active_host = host 
		if active_host == None:
		    active_host = hosts[0]

		vncview_href = ''
		if active_comp.display != '':
		    if active_comp.vnc_status != 'None' and active_comp.vnc_status != '':
		        vncview_href = 'http://' + active_host.ip + ':' + active_comp.get_port()
		
		data['control_active_comp'] = {'title': active_comp.title, 'status': active_comp.status, 
								'host_ip': active_host.ip,'host_port': active_host.port,
								'href': active_comp.href, 'start': active_comp.start,
								'vars':  active_comp.vars, 'log': active_comp.log, 
				                            	'stop': active_comp.stop , 'display': active_comp.display,
								'parent': active_comp.parent,
								'isGroup':active_comp.isGroup,
								'priority':active_comp.priority,
								'status_cmd': active_comp.status_cmd,
								'privilege': active_comp.privilege,
								'vnc_status': active_comp.vnc_status, 'tail_out': active_comp.tail_out,
								'err': active_comp.err, 'vncview_href': vncview_href,
								'hasChilds': active_comp.hasChilds(comps, self.privilegeLevel)}
		
		# Start Tree Order
		startTreeOrder = []
		if not active_comp.isGroup:
			startTreeOrder.append(active_comp.title)

		self.addAllChildrenToList(comps, active_comp, startTreeOrder)
		data['startTreeOrder'] = startTreeOrder
		


		self.env.log.info('Refresh ' + refresh)       
		self.env.log.info("control_active_comp")
		self.env.log.info(data['control_active_comp'])
		add_script(req, 'cl/js/framework.js')
		add_script(req, 'cl/js/ajax.js')			 
		add_stylesheet(req, 'cl/css/ajax.css')			 
		add_stylesheet(req, 'cl/css/control.css')    
		add_stylesheet(req, 'cl/css/guestbook.css')
	
		self.timestamp("Page will be rendered now")

		return 'control.html', data, None


############## lokale Methode(n) ################


	def get_button_labels(self, req, active_comp ):
		ret = {'op': '', 'vnc_op': '' }

		hasPriv = self.privilegeLevel >= active_comp.privilege

		if not active_comp.isGroup:
			if 'Verbindung' in active_comp.err:
				active_comp.status = 'unknown' 
#				if hasPriv:
#					ret['op'] = 'wakeonlan'
				return ret

			if 'windows' in active_comp.vnc_status:
				active_comp.status = 'unknown' 
				return ret

			if active_comp.status == '':
				active_comp.status = 'inactive'
				if hasPriv:
					ret['op']  = 'start'
			else:
				active_comp.status = 'active (pid ' + str(active_comp.status) + ' )'
				if hasPriv:
					ret['op']  = 'quit'

			if active_comp.display != '':

				if active_comp.vnc_status == '':
					if hasPriv: 
						ret['op']  = ''
						ret['vnc_op'] = 'vnc_start'             
			
				elif str(active_comp.vnc_status) in 'None':
					if hasPriv:
						if 'aktiv' in active_comp.status and 'inactive' not in active_comp.status :
							ret['op']  = 'quit'
						else: 
							ret['op']   = ''
						ret['vnc_op'] = ''
				else:
					if hasPriv:
						if 'aktiv' in active_comp.status and 'inactive' not in active_comp.status:
							ret['vnc_op']  = ''
						else:
							ret['vnc_op']  = 'vnc_quit'        
		return ret


	# Needed For StartingTreeOrder
	def addAllChildrenToList(self, comps, parent, clist):
		for comp in comps:
			if comp.parent == parent.title:
				if not comp.isGroup:
					clist.append(comp.title)
				self.addAllChildrenToList(comps, comp, clist)
