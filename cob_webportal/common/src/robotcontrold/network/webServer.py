import threading, time, base64, datetime, urllib, urllib2, json, urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from utils.eventHistory import EventHistory
from utils import privileges
from myExceptions.webServerExceptions import *
from myExceptions.networkExceptions import *


class WebServer(threading.Thread):
    SERVER_AVAILABLE = 1
    SERVER_IN_CHARGE = 2
    SERVER_NOT_AVAILABLE = -1
    
    def __init__(self, serverThread, log, port=8000):
        threading.Thread.__init__(self)

        self.log = log

        self.httpServer = None
        self.serverThread = serverThread
        self.alive = False

        self.log.info ("Creating WebServer on port %d" % port)
        self.httpServer = MyHTTPServer(serverThread, self.log, ('', port), MyHandler)

        self.alive = False


    def __del__(self):
        # stop the server in order to close all open connections. Stop should be normally
        # called anyway. 
        self.stop()


    # @Override 
    def start(self):
        if not self.alive:
            self.log.debug('Starting WebServer')
            self.alive = True
            threading.Thread.start(self)
            
    def checkAccess(self):
        pass;


    def stop(self):
        if self.alive:
            self.log.debug('Stopping WebServer')
            self.alive = False
            self.httpServer.shutdown()


    def isAlive(self):
        return self.alive


    def run(self):
        self.log.debug('Serve forever')
        self.httpServer.serve_forever()
        


class MyHTTPServer(HTTPServer):
    def __init__(self, serverThread, log, opt, handle):
        self.serverThread = serverThread
        HTTPServer.__init__(self, opt, handle)

        self.log = log

        self.protocol_version = 'HTTP/1.1'

        

class MyHandler(BaseHTTPRequestHandler):
    
    def __init__(self, *args):
        BaseHTTPRequestHandler.__init__(self, *args)    


    def do_GET(self):
        serverThread = self.server.serverThread
        activeUser = serverThread.activeUser

        try:
            responseCode = 200
            args = {}
            options = {}
            output = None

            try:
                auth = None
                if self.headers.has_key('Authorization'):
                    userPass = None
                    auth = {'token': str(self.headers['Authorization'])}
                    if auth[ 'token' ].lower().startswith( 'basic' ):
                        # remove the leading "Basic " before splitting into user/pass
                        userPass = base64.b64decode(auth['token'][6:]).split(':')
                    elif auth[ 'token' ].lower().startswith( 'localhost' ):
                        host, port = self.client_address
                        if  host != 'localhost' and host != '127.0.0.1':
                            raise UnauthorizedRequestError( 'Only allowed by localhost', self.path )
                        name = auth[ 'token' ][ 10: ]
                        userPass = [ name, '' ]
                    else:
                        raise UnauthorizedRequestError( 'Illegal token: %s' % auth[ 'token' ], self.path) 

                    if len(userPass) != 2:
                        auth = None
                        self.server.log.warn('Invalid Authorization Header: %s', str(self.headers['Authorization']))
                    else:
                        # important: always process names in lowercase
                        auth['user'] = userPass[0].lower()
                        auth['pass'] = userPass[1]
                        if not activeUser:
                            auth['status'] = WebServer.SERVER_AVAILABLE
                        elif activeUser and activeUser.name == auth['user']:
                            auth['status'] = WebServer.SERVER_IN_CHARGE
                        else:
                            auth['status'] = WebServer.SERVER_NOT_AVAILABLE
                    
                
                # if no auth was sent, return an 401 Unauthorized
                if not auth:
                    raise UnauthorizedRequestError('No Auth-Token received', self.path)
                
                
                # get the request user
                requestUser = serverThread.getUserCreateIfNotExistent(auth['user'])
                

                # split the path by the first ?
                argsString, optionsString = self.path.split('?', 1) if self.path.find('?') > 0 else (self.path, '')

                # parse the request (remove the leading and trailing / , then split by /)
                args = argsString.strip('/').split("/")

                # parse the options string
                temp = optionsString.split('&')
                for t in temp:
                    key, value = t.split('=',1) if t.find('=') > 0 else (t, '')
                    if key:
                        value = urllib2.unquote( urllib2.unquote(value)).replace( '+', ' ' ) if value else None
                    options[key] = value
                    

                # action is the first argument
                action = args[0]
                
                # Status Command must be available even if no user is logged in
                if action == 'status':
                    output = '{"status": %d}' % auth['status']
                    
                    
                elif action == 'info':
                    output  = '[Path]<br>%s<br>' % str(self.path)
                    output += '<br>'
                    
                    output += '[Args]<br>%s<br>' % str(args)
                    output += '<br>'
                    
                    output += '[Options]<br>%s<br>' % str(options)
                    output += '<br>'

                    output += '[ActiveUser]<br>'
                    if activeUser:
                        output += 'name:%s<br>' % activeUser.name
                    else:
                        output += 'None<br>'
                    output += '<br>'
                    
                    output += '[RequestUser]<br>name:%s<br>' % requestUser.name
                    output += '<br>'

                    output += '[Components]<br>'
                    for comp in requestUser.components():
                        output += '%s<br>' % str(comp)
                    output += '<br>'


                    output += '[Hosts]<br>'
                    for host in serverThread.hosts.values():
                        output += '%s<br>' % str(host)
                    output += '<br>'    
                    
                    output += '[Auth]<br>'
                    if not auth:
                        output += 'None'
                    else:
                        output += 'token: %s<br>' % auth['token']
                        output += 'user: %s<br>' % auth['user']
                    output += '<br>'
                    
                    output += '[Permission]<br>'
                    output += "Bitmask:       %s<br>" % str(requestUser.getPrivileges())
                    output += "ACTION_RUN:    %s<br>" % str(requestUser.hasPrivilege(privileges.ACTION_RUN))
                    output += "ACTION_STOP:   %s<br>" % str(requestUser.hasPrivilege(privileges.ACTION_STOP))
                    output += "ACTION_STATUS: %s<br>" % str(requestUser.hasPrivilege(privileges.ACTION_STATUS))
                    output += "COMP_ADMIN:    %s<br>" % str(requestUser.hasPrivilege(privileges.COMP_ADMIN))
                    output += "HOST_ADMIN:    %s<br>" % str(requestUser.hasPrivilege(privileges.HOST_ADMIN))
                    output += "START_SERVER:  %s<br>" % str(requestUser.hasPrivilege(privileges.START_SERVER))
                    output += "PRIV_ADMIN:    %s<br>" % str(requestUser.hasPrivilege(privileges.PRIV_ADMIN))
                    


                # privileges
                elif action == 'privileges':
                    if len(args) < 2:
                        raise ArgumentRequestError('Wrong argument count for "privileges". %s found, at least 2 Required.' % str(args), self.path)
                        
                    if args[1] == 'my':
                        output = str(requestUser.getPrivileges()) 
                        
                    elif args[1] == 'all':
                        if not requestUser.hasPrivilege(privileges.PRIV_ADMIN):
                            raise UnauthorizedRequestError('Insufficient rights.', self.path)
                        allUsersPermission = serverThread.allUsersPermission();
                        output = json.dumps({'labels': privileges.dict(), 'users': allUsersPermission})
                        
                    elif args[1] == 'submit':
                        if not requestUser.hasPrivilege(privileges.PRIV_ADMIN):
                            raise UnauthorizedRequestError('Insufficient rights.', self.path)
                        serverThread.savePermissions(options)
                        output = "Ok."
                        
                    else:
                        raise ArgumentRequestError('Invalid Argument for privileges "%s". ' % str(args[1]), self.path)
                        
                        
                    
                    
                # Request host / component data
                elif action == 'data':
                    # data/(host|comp)
                    if len(args) < 2:
                        raise ArgumentRequestError('Wrong argument count for "data". %s found, at least 2 Required.' % str(args), self.path)

                    
                    if args[1] == 'host':
                        JSONObj = {}
                        
                        for host in serverThread.hosts.values():
                            JSONObj[host.id] = host.createJSONObj()
                        output = json.dumps(JSONObj)
                        
                    
                    #TODO: use json dump a la json.dump(comp.webInformation)!
                    elif args[1] == 'comp':
                        JSONObj = {}

                        for comp in requestUser.components():
                            JSONObj[comp.id] = comp.createJSONObj();
                        output = json.dumps(JSONObj)    
                        
    
                    # Events                    
                    elif args[1] == 'eventHistory':
                        # you must be in charge
                        if not auth['status'] == WebServer.SERVER_IN_CHARGE:
                            raise UnauthorizedRequestError('You are not in charge.', self.path)
                        
                        if len(args) != 3:
                            raise ArgumentRequestError('Wrong argument count for "data/eventHistory". %s found, 3 Required.' % str(args), self.path)
                        
                        if not args[2].isdigit():
                            raise ArgumentRequestError('Invalid argument for timestamp "%s". timestamp must be numerical.' % args[2], self.path)
                        
                        timestamp = int(args[2])
                        data = EventHistory.getEventData(timestamp)
                        #TODO: use json dump
                        outputObject = { "timestamp": time.time(), "events": data }
                        output = json.dumps( outputObject )
                        
                        
                    else:
                        raise ArgumentRequestError('Invalid Argument for data "%s". ' % str(args[1]), self.path)
                
                
                elif action == 'parameters':
                    # you must be in charge
                    if not auth['status'] == WebServer.SERVER_IN_CHARGE:
                        raise UnauthorizedRequestError('You are not in charge.', self.path)
                    try:
                        command = args[ 1 ]
                        compId = int( args[ 2 ])
                        actionId = int( args[ 3 ]) 
                    except ( ValueError, KeyError, IndexError ) as e:
                        raise ArgumentRequestError( 'Wrong format for parameter', self.path )
                    if command not in ( 'load', 'save' ):
                        raise ArgumentRequestError( 'Wrong command type', self.path )


                    comp = activeUser.get(compId)
                    if not comp:
                        raise ArgumentRequestError('Component with id "%d" not found' % compId, self.path)
                    action = comp.getAction(actionId)
                    if not action:
                        raise ArgumentRequestError('Action "%d" for component "%d, %s" not found.' % (actionId, compId, comp.getName()), self.path)


                    if command == 'load':
                        parameters = serverThread.loadParameters( comp, action )
                        output = parameters


                    if command == 'save':
                        try:
                            print options[ 'json' ]
                            data = json.loads( options['json'] )
                            print data
                        except KeyError, e:
                            raise ArgumentRequestError( 'Data Field missing', self.path  )
                        except ValueError, e:
                            raise ArgumentRequestError('Could not decode json Object:\n%s' % options['json'], self.path)
                        if serverThread.saveParameters( comp, action, data ):
                            output = '{"success": true}'
                        else:
                            output = '{"success": false}'


                
                # Start/Stop/Kill/Request status of an action
                elif action == 'exec':
                    # you must be in charge
                    if not auth['status'] == WebServer.SERVER_IN_CHARGE:
                        raise UnauthorizedRequestError('You are not in charge.', self.path)
                    
                    if len(args) != 4:
                        raise ArgumentRequestError('Wrong argument count for "exec". %s found, 4 Required.' % str(args), self.path)

                    if not args[1].isdigit():
                        raise ArgumentRequestError('Invalid argument for compId "%s". compId must be numerical.' % args[1], self.path)
                    if not args[2].isdigit():
                        raise ArgumentRequestError('Invalid argument for actionId "%s". actionId must be numerical.' % args[2], self.path)

                    compId = int(args[1])
                    actionId = int(args[2])
                    command = args[3]

                    comp = activeUser.get(compId)
                    if not comp:
                        raise ArgumentRequestError('Component with id "%d" not found' % compId, self.path)

                    action = comp.getAction(actionId)
                    if not action:
                        raise ArgumentRequestError('Action "%d" for component "%d, %s" not found.' % (actionId, compId, comp.getName()), self.path)


                    if command == 'start':
                        # check privileges
                        if not requestUser.hasPrivilege(privileges.ACTION_RUN):
                            raise UnauthorizedRequestError('You have no privileges to run an action', self.path)
                        result = action.start( requestUser.globalVars )
                    elif command == 'stop':
                        # check privileges
                        if not requestUser.hasPrivilege(privileges.ACTION_STOP):
                            raise UnauthorizedRequestError('You have no privileges to stop an action', self.path)
                        result = action.stop( requestUser.globalVars )
                        
                    elif command == 'kill':
                        # check privileges
                        if not requestUser.hasPrivilege(privileges.ACTION_STOP):
                            raise UnauthorizedRequestError('You have no privileges to kill an action', self.path)
                        result = action.kill()
                        
                    elif command == 'isAlive':
                        result = action.isAlive()

                    elif command == 'status':
                        # check privileges
                        if not requestUser.hasPrivilege(privileges.ACTION_STATUS):
                            raise UnauthorizedRequestError('You have no privileges to show the status of an action', self.path)
                        result = action.status()
                    else:
                        raise ArgumentRequestError('Invalid Command "%s".' % command, self.path)

                    output =  str(result)
            
            
                # Reservations
                elif action == 'reservations':
                    if len(args) < 2:
                        raise ArgumentRequestError('At least 2 Parameters expected. Received: %s' % str(args), self.path)
                    
                    if args[1] == 'get':
                        output = '{'
                        data = serverThread.reservations
                        for id in data.keys():
                            reservation = data[id]
                            if reservation:
                                #TODO: use json dump
                                title = '%s %s - %s' % (reservation['user'].name, reservation['start'].strftime('%H:%M'), reservation['end'].strftime('%H:%M'))
                                owner = 'true' if reservation['user'] == requestUser else 'false'
                                start = reservation['start'].strftime('%Y-%m-%d-%H-%M')
                                end = reservation['end'].strftime('%Y-%m-%d-%H-%M')
                                output += '"%d": {"title": "%s", "owner": %s, "start": "%s", "end": "%s"},' % (id, title, owner, start, end)
                        output = output.strip(',') + '}'
                        
                        
                    elif args[1] == 'add':
                        if len(args) != 4:
                            raise ArgumentRequestError('4 Parameters expected. Received: %s' % str(args), self.path)
                        
                    
                        # decode start / end date
                        try:
                            start_date = datetime.datetime.strptime(args[2], "%Y-%m-%d-%H-%M")
                            end_date = datetime.datetime.strptime(args[3], "%Y-%m-%d-%H-%M")
                        except Exception, e:
                            raise ArgumentRequestError('Start-Date or End-Date invalid ["%s", "%s"]' % (args[2], args[3]), self.path)

                        #serverThread.addReservation
                        output = str(serverThread.addReservation(requestUser, start_date, end_date))
                        
                        
                    elif args[1] == 'extend':
                        if len(args) != 4:
                            raise ArgumentRequestError('4 Parameters expected. Received: %s' % str(args), self.path)
                        
                    
                        # decode start date
                        try:
                            end_date = datetime.datetime.strptime(args[3], "%Y-%m-%d-%H-%M")
                        except Exception, e:
                            raise ArgumentRequestError('End-Date invalid ["%s"]' % args[3], self.path)

                        try:
                            id = int(args[2])
                        except ValueError, e:
                            raise ArgumentRequestError('Invalid Reservation id passed', self.path)
                        
                        try:
                            serverThread.extendReservation(id, end_date, requestUser)
                        except ValueError,e:
                            raise ArgumentRequestError(str(e), self.path)
                        
                        output = "OK"
                        
                        
                        
                    elif args[1] == 'kill':
                        if len(args) != 3:
                            raise ArgumentRequestError('3 Parameters expected. Received: %s' % str(args), self.path)
                        
                        try:
                            id = int(args[2])
                        except ValueError, e:
                            raise ArgumentRequestError('Invalid Reservation id passed', self.path)
                        
                        try:
                            serverThread.killReservation(id, requestUser)
                        except ValueError,e:
                            raise ArgumentRequestError(str(e), self.path)

                        output = "OK"
                        
                        
                    else:
                        raise ArgumentRequestError('Unexpected reservations argument "%s"' % args[2], self.path)
                    
                    
                    
                    
                # store a component when changed
                elif action == 'store':
                    if len(args) < 2:
                        raise ArgumentRequestError('At least 2 arguments expected. Received: %s' % str(args), self.path)


                    if args[1] == 'component':
                        # You need COMP_ADMIN rights to perform this action
                        if not requestUser.hasPrivilege(privileges.COMP_ADMIN):
                            raise UnauthorizedRequestError('You have no privileges to change a component', self.path)


                        if not 'json' in options:
                            raise ArgumentRequestError('json parameter not received. Received options: %s' % str(options), self.path)
                    
                        try:
                            jsonObject = json.loads(options['json'])
                        except Exception, e:
                            self.server.log.error('Decoding JSON: --- \n%s\n --- failed' % options['json'])
                            raise ArgumentRequestError('Could not decode json Object:\n%s' % options['json'], self.path)
                            
                        idMap = serverThread.storeComponent(jsonObject, requestUser)
                        output = json.dumps(idMap)


                    if args[1] == 'host':
                        # You need HOST_ADMIN rights to perform this action
                        if not requestUser.hasPrivilege(privileges.HOST_ADMIN):
                            raise UnauthorizedRequestError('You have no privileges to change a host', self.path)
                        
                        if len(args) != 7:
                            raise ArgumentRequestError('7 arguments expected. Received: %s' % str(args), self.path)

                        if not auth['status'] == WebServer.SERVER_IN_CHARGE:
                            raise UnauthorizedRequestError('You are not in charge.', self.path)


                        id = args[2]
                        hostname = args[3]
                        username = args[4]
                        password = args[5]
                        port = args[6]
                        output = json.dumps(serverThread.storeHost(id, hostname, username, password, port))
                  
                elif action == 'install':
                    # You need COMP_INSTALL rights to perform this action
                    #if not requestUser.hasPrivilege(privileges.COMP_INSTALL):
                    #    raise UnauthorizedRequestError('You have no privileges to delete a component', self.path)
                    
                    if not 'pkg' in options:
                        raise ArgumentRequestError( 'No Package name passed as argument', self.path )
                        
                    if not 'host' in options:
                        raise ArgumentRequestError( 'No Host specified', self.path )
                    
                    log, startCommand, stopCommand = serverThread.installPackage( options['pkg'], options['host'] )
                    output = json.dumps({"success": True, "log": log, 'startCommand': startCommand, 'stopCommand': stopCommand})


                # delete a component
                elif action == 'delete':
                    # You need COMP_ADMIN rights to perform this action
                    if not requestUser.hasPrivilege(privileges.COMP_ADMIN):
                        raise UnauthorizedRequestError('You have no privileges to delete a component', self.path)

                    
                    if len(args) != 2:
                        raise ArgumentRequestError('No componentId passed as argument', self.path)
                    
                    requestUser.deleteComponent(args[1])
                    serverThread.saveUser(requestUser)
                    output = '{"success": true}'



                elif action == 'globals':
                    if len( args ) != 2:
                        raise ArgumentRequestError( 'No Action defined for global' )
                    
                    if args[ 1 ] == 'save':
                        requestUser.globalVars = options
                        output = '{"success": true }'
      
                    elif args[ 1 ] == 'get':
                        output = json.dumps( requestUser.globalVars )

                else:
                    raise UnknownRequestError('Unknown request. Args: %s.' % str(args), self.path)
                
                
                
                # if output was not set, raise an error 
                if not output:
                    raise UnknownRequestError('The request did not produce any output. Args: %s' % str(args), self.path)

            except NoConnectionToHostException as e:
                # host is not connected
                responseCode = 404
                output = '404 Host is not connected'

            except ArgumentRequestError as e:
                # statusCode 400 Bad Request
                responseCode = 400
                output = '400 %s' % str(e)

            except UnauthorizedRequestError as e:
                # statusCode 401 Unauthorized
                responseCode = 401
                output = '401 %s' % str(e)

            except UnknownRequestError as e:    
                # statusCode 404 Not Found
                responseCode = 404
                output = '404 %s' % str(e)

            except Exception as e:
                # statusCode 500 Internal Server Error
                responseCode = 500
                output = '500 Internal Server Error: %s' % str(e)
                self.server.log.exception('An error occured parsing the request')


            self.send_response(responseCode)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
#           self.server.log.debug(output)
#           self.wfile.write(output)#.encode('ascii'))

            if not 'repr' in options:
                self.wfile.write(output.encode('ascii','ignore'))
            else:
                self.wfile.write(repr(output).encode('ascii','ignore'))

        except Exception as e:
            self.server.log.exception('An error occured sending the request', e)
            traceback.print_exc()


    # Logging produces too much output
    def log_request(self, code='-', size='-'):
        #       self.server.log.debug('Request: "%s" %s %s' % (self.requestline, str(code), str(size)))
        pass

    def log_error(self, format, *args):
        self.server.log.error(format%args)
    
