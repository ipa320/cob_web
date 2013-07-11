class CorruptDatabaseError(Exception):
	def __init__(self, msg):
		Exception.__init__(self, 'The database seems to be corrupt.\n%s' % msg)
