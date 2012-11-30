
class UnknownRequestError(Exception):
	def __init__(self, string, request):
		Exception.__init__(self, '%s\nRequest: %s' % (string, request))

class UnauthorizedRequestError(Exception):
	def __init__(self, string, request):
		Exception.__init__(self, '%s\nRequest: %s' % (string, request))

class ArgumentRequestError(Exception):
	def __init__(self, string, request):
		Exception.__init__(self, '%s\nRequest: %s' % (string, request))


