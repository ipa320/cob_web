# Neue Version von RoboterZustand fuer die Template-Engine Genshi
# Portierung und Anpassung von Oezguer Sen
from setuptools import setup, find_packages

PACKAGE = 'RobotControl'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
	  #packages=find_packages(exclude=['*.tests*']),
      packages=['control'],
	  entry_points={'trac.plugins': '%s = control' % PACKAGE},
      #entry_points={'trac.plugins': 'mycontrol = control.control'},
      package_data={'control': ['htdocs/css/*.css', 'htdocs/images/*.*', 'htdocs/js/*.js', 'templates/*.html']},
      author = 'Regina Klauser , Oezguer Sen',
      author_email = 'oezguer.sen@ipa.fhg.de',
      description = 'Webinterface to start/stop robot components and view component logs. Autorin: Regina Klauser. Ueberarbeitete und portierte Version der Komponente auf Genshi von Oezguer Sen',
      license = 'GPL'
      )


