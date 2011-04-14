## @package ControlPlugin
# -*- coding: utf8 -*-
#  Trac-plugin for robot process control
#  
#  @author: Regina Klauser
#  @license: BSD License
#
from robothost import *
from robotcomp import *
from backgroundServerClient import *
import sqlite3
from operator import itemgetter, attrgetter
import re
from trac.web.chrome import add_script


localhost_id = 1

def control_admin( db, req, href, log, data={} ):
	global localhost_id   
    
	nav_list = []
	comp_list = []
	display_attrs = []
	comps = None
	
	data['controladmin_mask'] = req.args.get( 'attr' )
	data['controladmin_mask_new'] = 'false'
	data['controladmin_err'] = ''
	
    
    
	log.debug(req.args)
	if req.method == 'POST':
        
		tmp_host = None

		if str(req.args.get( 'attr' )) in 'None':    
			log.debug('attr = None') 
			return ''
        
		sql = ''     
        
		if str(req.args.get( 'attr' )) in 'comp' or str(req.args.get( 'attr' )) in 'grp':  
			if str(req.args.get( 'attr' )) in 'comp':
				ret, tmp_comp = check_comp_changes( req, localhost_id, href )
			else:
				ret, tmp_comp = check_grp_changes( req, localhost_id, href )

			if ret == False:
				data['controladmin_err'] += u'''Die Skriptkonfiguration konnte nicht aktualisiert werden.\n
                                               Bitte \xfcberpr\xfcfen Sie Ihre Angaben in den Pflichtfeldern. Bemerkung: Der Titel einer Komponente / Gruppe darf nicht "Neu" lauten. '''   
			log.debug('COMPADMIN')
			''' COMPADMIN '''
			if req.args.get( 'delete' ):  
				if ret != False:      
					sql = tmp_comp.delete()                                             
				log.debug('SQL for deleting a component: ') 
				log.debug(sql)
				url = '/admin?operation=new&attr=comp'
			elif req.args.get( 'update' ):
				if ret != False:      
					sql = tmp_comp.update(tmp_comp)                          
				log.debug('SQL for updating a component: ') 	
				log.debug(sql)
				url = '/' + tmp_comp.title 
			elif req.args.get( 'new' ): 
				if ret != False:      
					sql = tmp_comp.create()
				log.debug( 'SQL for creating a component: ')
				log.debug(sql)
				url = '/' + tmp_comp.title 
			else:
				url = '/admin?operation=refresh&attr=comp'    

        
		elif str(req.args.get( 'attr' )) in 'host':              
            
			ret, tmp_host = check_host_changes( req, href )
			if ret == False:
				data['controladmin_err'] += u'''Die Hostkonfiguration konnte nicht aktualisiert werden.\n
                                               Bitte \xfcberpr\xfcfen Sie Ihre Angaben in den Pflichtfeldern.'''
			log.debug('HOSTADMIN')
			''' HOSTADMIN '''
			if req.args.get( 'delete' ): 
				log.debug('req[id] in delete:' + str(req.args.get( 'id' )))
#                for host in hosts:
#                    log.debug('HOST:' + str(host.id))
#                    if req.args.get( 'id' ) and int(host.id) == int(req.args.get( 'id' )): 
#                        log.debug('BINGO!')  
				if ret != False:
					sql = tmp_host.delete()
				log.debug( 'SQL for deleting a host: ')
				log.debug(sql)       
				url = '/admin?operation=new&attr=host'
				data['controladmin_mask'] = 'host'
				data['controladmin_mask_new'] = 'true'
						
                
			elif req.args.get( 'update' ):
				if ret != False:
					sql = tmp_host.update(tmp_host)
				log.debug( 'SQL for updating a host: ')
				log.debug(sql)   
				url = '/admin?operation=refresh&attr=host'
				data['controladmin_mask'] = 'host'
				data['controladmin_mask_new'] = 'false'
                
			elif req.args.get( 'new' ):  
                
				if ret != False:
					sql = tmp_host.create(tmp_host)
					url = '/admin?operation=refresh&attr=host&id=' + tmp_host.id
					data['controladmin_mask'] = 'host'
					data['controladmin_mask_new'] = 'false'
			else:
				url = '/admin?operation=refresh&attr=host' 
            
       
                    
		if sql == '':
			data['controladmin_err'] += u'''Nichts passiert. '''
			log.debug('Nichts passiert.')
          #  req.redirect(href+ url )
#		try:
		for query in sql:
			db.cursor().execute( query )
			db.commit()

		# Resort the items
		sortComponents(req, db, href)

		# Update the sync id
		query = "UPDATE `robot_settings` SET `value`=`value`+1 WHERE `key`='SyncID'"
		db.cursor().execute( query )
		db.commit()

		# restart the background server if the host depended on it
		if tmp_host and tmp_host.useBgrndServer:
			bgrndServer = BackgroundServerClient(tmp_host)
			try:
				bgrndServer.connectAndRestart()
			except Exception,e:
				data['controladmin_err'] += u"Es ist ein Fehler aufgetreten: Konnte den Background-Server nicht neustarten"
				log.debug ('Could not restart the background-server: ' + str(e))
				tmp_host.set_err('Could not restart the background-server: ' + str(e))

#            req.redirect(href+ url )
#		except sqlite3.IntegrityError, e:
#			data['controladmin_err'] += u'''Es ist ein Fehler aufgetreten.''' +  str(e.args[0])
#			data['controladmin_err'] += '''Bitte pruefen Sie, ob diese Komponente oder Host bereits existiert.'''
#
 #           
#		except sqlite3.Error, e: # sqlite3.IntegrityError  
#			data['controladmin_err'] += 'Es ist ein Fehler aufgetreten; Mysql-Result: ' + str(e.args[0]) + '; Sql: ' + query
#			log.debug(req.args.get( 'An error ocurred: ' + e.args[0])) 
    
    
	hosts = get_hosts( db.cursor(), req, href, 'admin')
	        	
	
	if hosts == None and not req.args.get( 'new' ):             
		''' NoHosts '''
		log.debug('No hosts found in the database.' )
        
		nav_list.append( ( '', 'Neuer Host', '', href + '/admin?operation=new&attr=host') )
		data['controladmin_hosts'] = nav_list
		display_attrs.append({'id': '', 'ip': '', 'user': '', 
                                 'passwd': '', 'mac': '', 'vnc_start': '', 'vnc_stop':'',
                                 'port': '', 'os': '', 'vncgrep': ''})
		data['controladmin_attrs'] = display_attrs 
		data['controladmin_mask'] = 'host'
		data['controladmin_mask_new'] = 'true'
        
		return None
    
	if hosts != None and  str(req.args.get( 'attr' )) != 'host':
		log.debug('hosts != None')
        
		comps = get_comps( db.cursor(), req, hosts, href, log, 'admin')
        
		if comps == None and not req.args.get( 'new' ):
			''' NoComponents '''
			log.debug('No comps found in the database.' )
			nav_list.append( ( 'Neue Komponente', href + '/admin?operation=new&attr=comp', '', 'null', '') )
			nav_list.append( ( 'Neue Gruppe', href + '/admin?operation=new&attr=grp', '', 'null', '') )
			data['controladmin_comps'] = nav_list
			display_hosts = []
			for host in hosts:
				display_hosts.append({'id': host.id, 'ip': host.ip, 'port': host.port })
				if host.ip in 'localhost':
					localhost_id = host.id         
			data['controladmin_hosts'] = display_hosts
            
			display_ids = []
			display_ids.append('None')
			for i in xrange(1,10):
				display_ids.append(str(i))      
			data['controladmin_display_id_list'] = display_ids 
			display_attrs.append({'title': 'New Component', 'search_name': '', \
                            'host_id': localhost_id, 'start': '', \
                            'vars':  '', 'log': '', \
                            'tail_length': '', 'stop': '', \
                            'display': '', 'parent':'', 'isGroup': False, 'privilege':2, 'priority':'null'})
			data['controladmin_attrs'] = display_attrs
			data['controladmin_mask'] = 'comp'
			data['controladmin_mask_new'] = 'true'          
			return None       
    
    
	'''Left side menu'''                     
	if str(req.args.get( 'attr' )) == 'comp' or str(req.args.get( 'attr' )) == 'grp':
		# add the ajaxAdmin
		add_script(req, 'cl/js/ajaxAdmin.js')


		if req.args.get('operation') == 'new':
			nav_list.append( ( 'Neu', '', '', -1, '') )

		if comps != None:
			for comp in comps:
				nav_list.append( ( comp.title, href + '/admin?operation=edit&attr=' + ('grp' if comp.isGroup else 'comp') + '&title=' + comp.title, comp.parent, int(comp.priority), re.sub(r'\s', '', comp.title) ) )
		else:
			req.redirect(href + '?advise=comp')

		nav_list.append( ( 'New Component', href + '/admin?operation=new&attr=comp', '', 'null', '') )
		nav_list.append( ( 'New Group', href + '/admin?operation=new&attr=grp', '', 'null', '') )
		log.debug(nav_list)

                    
		'''Attributes'''
		active_comp = comps[0]   
		if str(req.args.get('operation'))  not in 'new':   
			for comp in comps:               
				if  req.args.get( 'title' ) and comp.title in req.args.get( 'title' ) and len(comp.title) == len(req.args.get( 'title' )) :                        
					active_comp = comp
			log.debug('TITLE: ' + str(active_comp.title ), ' ISGROUP:' + str(active_comp.isGroup))        
		else:
			data['controladmin_mask_new'] = 'true'
			active_comp = RobotComp({'title': 'Neu', 'search_name': '', \
                            'host_id': localhost_id, 'start': '', \
                            'vars':  '', 'log': '', \
                            'tail_length': '', 'stop': '', \
                            'display': '', \
			    'parent': '', \
			    'privilege': 2, \
			    'priority':0, \
			    'status_cmd':'', \
			    'isGroup': (req.args.get( 'attr' ) in 'grp')}, href)
		data['activecomp'] = active_comp

		# Update the control_admin_mask. 
		data["controladmin_mask"] = 'grp' if active_comp.isGroup else 'comp'
		
        
		display_hosts = []
		for host in hosts:
			display_hosts.append({'id': host.id, 'ip': host.ip, 'port': host.port })
			if host.ip in 'localhost':
				localhost_id = host.id         
		data['controladmin_hosts'] = display_hosts


		''' Parents in the list '''
		for comp in comps:
			if not active_comp.contains(comps, comp):
				comp_list.append(comp.title)
        
		display_ids = []
		display_ids.append('None')
		for i in xrange(1, 10):
			display_ids.append(str(i))

		# Allow multiple display usage
#		for comp in comps:
#			if comp.display != active_comp.display:
#				try:
#					display_ids.remove(comp.display)    
#				except ValueError:
#					log.info(ValueError)              
            
		data['controladmin_display_id_list'] = display_ids
		display_attrs = [] 
		display_attrs.append( {'title': active_comp.title, \
                            'search_name': active_comp.search_name, \
                            'host_id': active_comp.host_id, \
                            'start': active_comp.start, \
                            'vars':  active_comp.vars, \
                            'log': active_comp.log, \
                            'tail_length': active_comp.tail_length, \
                            'stop':active_comp.stop,\
                            'display': active_comp.display, \
                            'parent': active_comp.parent, \
                            'isGroup': active_comp.isGroup, \
                            'privilege':active_comp.privilege, \
                            'priority':active_comp.priority, \
                            'status_cmd':active_comp.status_cmd }) 
    
	elif str(req.args.get( 'attr' )) in 'host':
		
		if hosts != None:
			for host in hosts:
				nav_list.append((host.id, host.ip, host.port, href + '/admin?operation=edit&attr=host&id='+ host.id ) )
		else:
			req.redirect(href + '?advise=host')
		
		nav_list.append( ( '', 'New Host', '', href + '/admin?operation=new&attr=host' ) )


		'''Attributes'''
		if str(req.args.get('operation'))  not in 'new':
			active_host = hosts[0]
            
			for host in hosts:               
				if req.args.get( 'id' ) and int(host.id) == int(req.args.get( 'id' )):
					active_host = host
		else:
			data['controladmin_mask_new'] = 'true'
			active_host = RobotHost({'id': '', 'ip': '', 'user': '', 
                                     'passwd': '', 'mac': '', 'vnc_start': '', 'vnc_stop': '',
                                     'port': '', 'os': '', 'vncgrep': '', 'useBgrndServer': True})

		data['activehost'] = active_host
		display_attrs = [] 
		display_attrs.append( {'id': active_host.id, 
                       'ip': active_host.ip, 
                       'user': active_host.user, 
                       'passwd': active_host.passwd, 
                       'mac': active_host.mac, 
                       'vnc_start': active_host.vnc_start, 
                       'vnc_stop': active_host.vnc_stop,
                       'port': active_host.port, 
                       'os': active_host.os, 
                       'vncgrep': active_host.vncgrep,
                       'useBgrndServer': active_host.useBgrndServer})

	data['controladmin_complist'] = comp_list
	data['controladmin_navitems'] = nav_list
	data['controladmin_attrs'] = display_attrs
        
         
def check_comp_changes( req, localhost_id, href ):

    attr_name_list = ['title', 'search_name', 'host_id', 'start', 'vars', 'log', 'tail_length', 'stop', 'display', 'parent', 'isGroup', 'privilege', 'priority', 'status_cmd']
    attr_changes = {}           
    
    for i in xrange(0, len(attr_name_list)):
        if req.args.get(attr_name_list[i]) == None:
            attr_changes[attr_name_list[i]] = ''
        else:
            attr_changes[attr_name_list[i]] = req.args.get(attr_name_list[i]).encode("utf8")
            if 'search_name' not in attr_name_list[i]:                 
                attr_changes[attr_name_list[i]] = attr_changes[attr_name_list[i]].strip()     
    
    comp = RobotComp( attr_changes,  href)
    
    if comp.host_id == '':
        comp.host_id = localhost_id
         
    if comp.log != '':
        if comp.tail_length == '' or comp.tail_length.isdigit() != True:
            comp.tail_length = '15'
    else: 
        comp.tail_length = ''

    # This is a comp, so set the attribute isGroup to false
    attr_changes['isGroup'] = False

    if comp.title == '' or comp.title == 'Neu' or \
     comp.start == '' or comp.search_name == '':
        return False, comp
    else:
        return True, comp


def check_grp_changes( req, localhost_id, href ):

    attr_name_list = ['title', 'search_name', 'host_id', 'start', 'vars', 'log', 'tail_length', 'stop', 'display', 'parent', 'isGroup', 'privilege', 'priority']
    attr_changes = {}           
    
    for i in xrange(0, len(attr_name_list)):
        if req.args.get(attr_name_list[i]) == None:
            attr_changes[attr_name_list[i]] = ''
        else:
            attr_changes[attr_name_list[i]] = req.args.get(attr_name_list[i]).encode("utf8")
            if 'search_name' not in attr_name_list[i]:                 
                attr_changes[attr_name_list[i]] = attr_changes[attr_name_list[i]].strip()     
    
    # This is a group, so set the attribute isGroup to true
    attr_changes['isGroup'] = True	

    # We set the host-id to -1 so it cannot be assigned any host
    attr_changes['host_id'] = -1

    comp = RobotComp( attr_changes,  href)
    

    if comp.title == '' or comp.title == 'Neu':
        return False, comp
    else:
        return True, comp
        

def check_host_changes( req, href ):
    
    attr_name_list = ['id', 'ip', 'user', 'passwd', 'mac', 'vnc_start', 'vnc_stop', 'port', 'os', 'vncgrep', 'useBgrndServer']
    attr_changes = {}           
    
    for i in xrange(0, len(attr_name_list)):
        if req.args.get(attr_name_list[i]) == None:
            attr_changes[attr_name_list[i]] = ''
        else:
            attr_changes[attr_name_list[i]] = req.args.get(attr_name_list[i]).encode("utf8")
            if 'search_name' not in attr_name_list[i]:                 
                attr_changes[attr_name_list[i]] = attr_changes[attr_name_list[i]].strip()                


    # the value of useBgrndServer is sent by a checkbox, so it's either "off" or "on"
    attr_changes['useBgrndServer'] = str(attr_changes['useBgrndServer']) == "on"

    # Return a new RobotHost object
    host = RobotHost( attr_changes )

    
    return True, host
#    if comp.log != '':
#        if comp.tail_length == '' or comp.tail_length.isdigit() != True:
#            comp.tail_length = '15'
#    else: 
#        comp.tail_length = ''
#
#    if comp.title == '' or comp.title == 'Neu' or \
#     comp.start == '' or comp.search_name == '':
#        return False, comp
#    else:
#        return True, comp           


def sortComponents(req, db, href):
	cursor = db.cursor()
	hosts = get_hosts(cursor, req, "")
	comps = get_comps(cursor, req, hosts, href, None )
	levelsCleared = []

	for comp in comps:
		if not comp.parent in levelsCleared:
			lvlCleared = sortCompLevel(comp, comps, cursor)
			levelsCleared.append(lvlCleared)
		
	db.commit()

		
def sortCompLevel(comp, comps, cursor):
	level = comp.parent
	unsorted = []
	
	for comp in comps:
		if comp.parent == level:
			unsorted.append(comp)
			

	sortedList = sorted(unsorted, key=attrgetter('priority', 'title'))

	for index, item in enumerate(sortedList):
		item.priority = index

		sql = item.update(item)
		for query in sql:
			cursor.execute(query)

	return level
