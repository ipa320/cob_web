from cgi import escape
from urllib import unquote

# The Publisher passes the Request object to the function
def index(req):
	width = str(req.form.getfirst('witdh'))
	width = int(width) if width.isdigit() else 1240
	
	height = str(req.form.getfirst('height'))
	height = int(height) if height.isdigit() else 932

	host = req.form.getfirst('host', '')

	port = str(req.form.getfirst('port'))
	port = int(port) if port.isdigit() else 5900

	code = """
<!-- 
     index.vnc - default HTML page for TightVNC Java viewer applet, to be
     used with Xvnc. On any file ending in .vnc, the HTTP server embedded in
     Xvnc will substitute the following variables when preceded by a dollar:
     USER, DESKTOP, DISPLAY, APPLETWIDTH, APPLETHEIGHT, WIDTH, HEIGHT, PORT,
     PARAMS. Use two dollar signs ($) to get a dollar sign in the generated
     HTML page.
 
     NOTE: the  variable is not supported by the standard VNC, so
     make sure you have TightVNC on the server side, if you're using this
     variable.
--> 
 
<HTML> 
<TITLE> 
webportal's X desktop (cob-sim2:2)
</TITLE> 
<APPLET CODE=VncViewer.class ARCHIVE=VncViewer.jar 
        WIDTH=1240 HEIGHT=932> 
<param name=HOST value=cob-sim2>
<param name=PORT value=8081> 
 
</APPLET> 
<BR> 
<A href="http://www.virtualgl.org/">TurboVNC site</A> 
</HTML> """

	return code# % (width, height, port, host)
