from utils.modules.module import Module
from utils.modules.component import Component
from utils.modules.group import Group


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
		if not isinstance(comp, Module):
			raise ValueError('Comp must be an instance of Module')

		self._items[comp.id] = comp


	# key must be the component's id
	# returns the component/group or None if not found
	def get(self, key):
		if not isinstance(key, int):
			raise ValueError('key must be an integer')

		if not key in self._items:
			return None

		return self._items[key]

	# key must be the component's id
	# returns the component or None if not found
	def getComponent(self, key):
		if not isinstance(key, int):
			raise ValueError('key must be an integer')

		if not key in self._items or not isinstance(self._items[key], Component):
			return None

		return self._items[key]


	# key must be the component's id
	# returns the group or None if not found
	def getGroup(self, key):
		if not isinstance(key, int):
			raise ValueError('key must be an integer')

		if not key in self._items or not isinstance(self._items[key], Group):
			return None

		return self._items[key]


	# return all ids i.e. keys() of components
	def getIDs(self):
		return self._items.keys()


	# used to iterate
	def iteritems(self):
		return self._items.iteritems()

	# used to iterate components only
	def itercomponents(self):
		return ((compId, comp) for (compId, comp) in self._items.iteritems() if isinstance(comp, Component))

	# used to iterate groups only
	def itergroups(self):
		return ((groupId, group) for (groupId, group) in self._items.iteritems() if isinstance(group, Group))

	# get all items
	def items(self):
		return self._items.values()

	# get all components
	def components(self):
		return list(comp for comp in self._items.values() if isinstance(comp, Component))

	# get all groups
	def groups(self):
		return list(group for group in self._items.values() if isinstance(group, Group))


