from utils.component import Component


class User():
	def __init__(self, name):
		# important: always process the name in lowercase
		self.name = name.lower()
		self._components = {}

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

		self._components[comp.id] = comp


	# key must be the component's id
	# returns the component/group or None if not found
	def get(self, key):
		if not isinstance(key, int):
			raise ValueError('key must be an integer')

		if not key in self._components:
			return None

		return self._components[key]
	
	# stub
	def getComponent(self, key):
		return self.get(key)
		
	def hasComponent(self, compId):
		return compId in self._components


	# return all ids i.e. keys() of components
	def getIDs(self):
		return self._components.keys()


	# used to iterate
	def iteritems(self):
		return self._components.iteritems()


	# get all items
	def components(self):
		return self._components.values()


