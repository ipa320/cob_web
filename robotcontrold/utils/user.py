from utils.component import Component


class User():
	def __init__(self, name):
		self.name = name
		self._items = {}

	def __str__(self):
		return 'User [name=%s]' % self.name

	def __eq__(self, obj):
		return isinstance(obj, User) and obj.name == self.name

	# The User is only defined by its name
	def __hash__(self):
		return self.name.__hash__()

	def append(self, comp):
		if not isinstance(comp, Component):
			raise ValueError('Comp must be an instance of Component')

		self._items[comp.id] = comp


	# key must be the component's id
	# returns the component/group or None if not found
	def get(self, key):
		if not isinstance(key, int):
			raise ValueError('key must be an integer')

		if not key in self._items:
			return None

		return self._items[key]


	# return all ids i.e. keys() of components
	def getIDs(self):
		return self._items.keys()


	# used to iterate
	def iteritems(self):
		return self._items.iteritems()


	# get all items
	def components(self):
		return self._items.values()


