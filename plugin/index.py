import os, urllib2

def index(req):
     #return loadPrivileges(req)
     index = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html/index.html'))
     result = ''
     for line in index:
          result += line
     
     return result

def loadPrivileges(req):
     # grab the privileges from the background server
     # make a request to .bs/permissions and pass the Authorization header
     # of the original request made to this page 
     hdl = urllib2.Request('http://%s/.bs/privileges' % req.hostname.strip('/') )
     hdl.add_header('Authorization', req.headers_in['Authorization'])
     response = urllib2.urlopen(hdl)
     return int(response.read())

