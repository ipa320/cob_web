# coding: utf-8
#Dieses Modul implementiert die SSH-Verbindung zu den jeweiligen hosts
#Damit man die Verbindung zu den Hosts parallel aufbauen kann, werden hier Thread-Objekte verwendet
#
#Um dieses Modul zu benutzen, muss das Paket python-paramiko installiert sein
#
# Author: Özgür Sen


from paramiko import *

import threading
import socket as socketImport



class SSHAccess(object):
	# Der Konstruktor beinhaltet nur die Wertzuweisung
	def __init__(self, hosts,log=None):
		self.hosts = hosts
		self.log=log
		
	# Für jeden einzelnen Host wird ein Thread gestartet um die Verbindung über ssh aufzubauen
	# Die Befehlsausführung und der SSH-Zugriff wird dabei von einem Thread-Objekt der Klasse HostAccessThread realisiert. 	
	# Diese Methode sorgt dafür, dass die Threads gestartet und dann wieder beendet werden
	#
	def startConnection(self):
		threadList = []
		
		for host in self.hosts:
			hostThread = HostAccessThread(host,log=self.log)
			threadList.append(hostThread)
			hostThread.start()
			
		for thread in threadList:
			thread.join()


# Diese Klasse hat die Funktion, für jeden Host ein Threading-Objekt zu erstellen, um damit die Verbindung aufzubauen, den Befehl auszuführen, 
# die Daten der Verbindung zu speichern und zum Schluss die Verbindung wieder zu beenden.
#
# Jedes Host-Objekt besitzt als Member eine Liste von Operations-Objekten.
# Für jedes einzelne Operations-Objekt werden die in ihm gespeicherten Operationen (Member: self.cmd) ausgeführt.
# Die Operations-Objekte haben weitere Member, in denen dann die Rückgabewerte bzw. Daten der SSH-Verbindung gespeichert werden.
class HostAccessThread(threading.Thread):

	def __init__(self, host,log=None):
		threading.Thread.__init__(self)
		self.client 	= SSHClient()
		self.host 	= host
		self.log	= log		

	def run(self):
		
		self.connectAndExecuteCommand()
		self.stopConnection()
		
	
	# Diese Methode baut die eigentliche Verbindung zum host auf.
	# Danach werden die Befehle aus der Operationsliste ausgeführt und die Rückgabewerte
	# den zughörigen Operations-Objekten zugewiesen bzw. gesetzt
	#
	# BEACHTE: 	Es ist wichtig, dass der SSH-Key auf Seiten des Clients (in dem Fall ist der Client das Webportal) bereits existiert. In der 
	#			Regel geschieht dies Automatisch, wenn man sich auf dem Client(Webportal)-Rechner mit einen Terminal über SSH auf einem Host 
	#			einloggt.
	#			Falls das nicht geschehen ist bzw. der Key nicht manuell erzeugt wurde, so muss dieser Schritt vorher gemacht werden! 
	#
	def connectAndExecuteCommand(self):
		if self.log != None:
			self.log.debug("Starting connection to host")

		self.client.load_system_host_keys()
		self.client.set_missing_host_key_policy(AutoAddPolicy())

		try:
			self.client.connect( self.host.ip, int(self.host.port), self.host.user, self.host.passwd)

		except:
			self.host.set_err('unreachable')
			
			for operation in self.host.operations:
				operation.err += 'Verbindungsversuch fuer %s ueber Port %s ist fehlgeschlagen.'%(self.host.ip, self.host.port)
			return
	
		for operation in self.host.operations:
			try:
				operation.set_result('')

				op_stdin, op_stdout, op_stderr = self.client.exec_command(operation.cmd)
				data  = unicode(op_stdout.read(), 'utf_8', errors='replace')
				error = unicode(op_stderr.read(), 'utf_8', errors='replace')

				if error != '':
					operation.set_err( u"operation nicht ausfuehrbar; siehe Log-Datei\n%s" % error )
			
				else:
					operation.set_result(data)

			except Exception,e:
				operation.set_err( u"An Exception occured along the way: %s" % str(e))

			
	def stopConnection(self):
		self.client.close()

class PermanentSSHConnection(object):

	def __init__(self, host,log=None):
		self.client 	= SSHClient()
		self.host 	= host
		self.log	= log
		self.connected	= False

	def connect(self):
		if not self.connected:
			self.client.load_system_host_keys()
			self.client.set_missing_host_key_policy(AutoAddPolicy())
			self.client.connect( self.host.ip, int(self.host.port), self.host.user, self.host.passwd)
			self.connected = True

	def disconnect(self):
		if self.connected:
			self.connected = False
			try:
				self.close()
			except Exception,e:
				pass
				

	def dateCheck(self):
		return self.execute("date")

	def isConnected(self):
		return self.connected

	def execute(self, cmd):
		try:
			op_stdin, op_stdout, op_stderr = self.client.exec_command(cmd)
			data  = unicode(op_stdout.read(), 'utf_8', errors='ignore')
			error = unicode(op_stderr.read(), 'utf_8', errors='ignore')
			return data, error
		except socketImport.error,e:
			self.disconnect()
			raise e


	def close(self):
#		if self.connected:
		self.client.close()
		self.connected = False
