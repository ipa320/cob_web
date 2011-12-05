from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
    add_stylesheet, add_javascript
from trac.web.main import IRequestHandler
from trac.util import escape, Markup
from genshi.builder import tag
import re, sqlite3, json




class RobotcontrolPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)


    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'robotcontrol'

    def get_navigation_items(self, req):
        yield ('mainnav', 'robotcontrol', tag.a('Robotcontrol',
                 href=self.env.href.robotcontrol() ) )


    # IRequestHandler methods
    def match_request(self, req):
    	# make sure the request doesn't end with a forward slash, otherwise
    	# problems occur when creating the forms
        return req.path_info.startswith( '/robotcontrol' ) and \
            req.path_info[-1] != '/'


    def loadPrivileges(self, req):
        import urllib2
        # grab the privileges from the background server
        # make a request to .bs/permissions and pass the Authorization header
        # of the original request made to this page 
        hdl = urllib2.Request('%s/.bs/privileges/my' % req.base_url)
        hdl.add_header('Authorization', req.get_header('Authorization'))
        response = urllib2.urlopen(hdl)
        return int(response.read())

    def hasPrivilege(self, privileges, bitmask):
        return (privileges & bitmask) == bitmask

    def process_request(self, req):
        add_javascript( req, 'htdocs/js/jquery-1.5.1.min.js' )
        add_javascript( req, 'htdocs/js/jquery-ui-1.8.13.custom.min.js')
        add_javascript( req, 'htdocs/js/application.js')
        add_javascript( req, 'htdocs/js/action.js')
#       add_javascript( req, 'htdocs/js/actionView.js')
        add_javascript( req, 'htdocs/js/actionEditView.js')
        add_javascript( req, 'htdocs/js/component.js')
        add_javascript( req, 'htdocs/js/componentView.js')
        add_javascript( req, 'htdocs/js/componentEditView.js')
        add_javascript( req, 'htdocs/js/logView.js')
        add_javascript( req, 'htdocs/js/styleDataManager.js')
        add_javascript( req, 'htdocs/js/screenManager.js')
        add_javascript( req, 'htdocs/js/dialogView.js')
        add_javascript( req, 'htdocs/js/menuView.js')
        add_javascript( req, 'htdocs/js/host.js')
        add_javascript( req, 'htdocs/js/infoBoxView.js')
        add_javascript( req, 'htdocs/js/calendarView.js')
        add_javascript( req, 'htdocs/js/hostManagerView.js')
        add_javascript( req, 'htdocs/js/userManagerView.js')
        add_javascript( req, 'htdocs/fancybox/jquery.fancybox-1.3.4.pack.js')
        add_javascript( req, 'htdocs/fullcalendar/fullcalendar.min.js')
        add_javascript( req, 'htdocs/js/json2.js')


        add_stylesheet( req, 'htdocs/Aristo/jquery-ui-1.8.7.custom.css')
#       add_stylesheet( req, 'htdocs/Aristo/jquery-ui-custom-icon.css')
#       add_stylesheet( req, 'htdocs/css/customJQuery.css')
        add_stylesheet( req, 'htdocs/css/actionEditView.css')
        add_stylesheet( req, 'htdocs/css/componentView.css')
        add_stylesheet( req, 'htdocs/css/componentEditView.css')
        add_stylesheet( req, 'htdocs/css/logView.css')
        add_stylesheet( req, 'htdocs/css/style.css')
        add_stylesheet( req, 'htdocs/css/dialogView.css')
        add_stylesheet( req, 'htdocs/css/infoBoxView.css')
        add_stylesheet( req, 'htdocs/css/adminBoxView.css')
        add_stylesheet( req, 'htdocs/css/userManagerView.css')
        add_stylesheet( req, 'htdocs/css/menuView.css')
        add_stylesheet( req, 'htdocs/fancybox/jquery.fancybox-1.3.4.css')
        add_stylesheet( req, 'htdocs/fullcalendar/fullcalendar.css')

        import privileges
        myPrivileges = self.loadPrivileges(req)
        options = { \
            'COMP_ADMIN': self.hasPrivilege(myPrivileges, privileges.COMP_ADMIN),
            'HOST_ADMIN': self.hasPrivilege(myPrivileges, privileges.HOST_ADMIN),
            'PRIV_ADMIN': self.hasPrivilege(myPrivileges, privileges.PRIV_ADMIN)
        }

		
    
        # default action
        # Markup to avoid escaping of the xml data
        return 'robotcontrol.html', options, None


    # ITemplateProvider methods
    def get_templates_dirs( self ):
        from pkg_resources import resource_filename
        return [resource_filename( __name__, 'templates' )]
        
    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [( 'htdocs', resource_filename( __name__, 'htdocs' ))]
