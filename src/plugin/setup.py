from setuptools import setup

PACKAGE = 'RobotControl'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['robotcontrol'],
      entry_points={'trac.plugins': '%s = robotcontrol' % PACKAGE},
      package_data={'robotcontrol': [
      	'htdocs/css/*.css',
     	'htdocs/js/*.js',
      	'htdocs/images/*',
      	
      	'htdocs/fullcalendar/*', 
      	'htdocs/fancybox/*',
      	'htdocs/Aristo/*.css',
      	'htdocs/Aristo/images/*',
      	'templates/*'
      ]}
)

