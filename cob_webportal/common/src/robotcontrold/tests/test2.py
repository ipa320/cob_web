
class Iterate():
	def __init__(self):
		self.dict = {'a':1, 'b':2, 'c':3, 'd':4}

	def iteritems(self):
		return self.dict.iteritems()

	def eveniter(self):
		return ((key,value) for (key,value) in self.dict.iteritems() if value%2==0)


if __name__=='__main__':
	iterate = Iterate()

	print 'Ordinary Iteritems'
	for key,value in iterate.iteritems():
		print '%s:%s' % (str(key), str(value))

	print
	print 'Tuples with Iteritems'
	for a in iterate.iteritems():
		print a

	print
	print 'No iteritems'
	try:
		for a in iterate:
			print a
	except Exception as e:
		print 'Error: %s' % str(e)

	print
	print 'Even iter'
	for key,value in iterate.eveniter():
		print '%s:%s' % (str(key), str(value))
