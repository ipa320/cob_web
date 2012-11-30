
class NoConnectionToHostException(Exception):
	def __init__(self, string):
		Exception.__init__(self, string)
