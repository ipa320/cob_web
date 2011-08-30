from utils.component import Component
from utils import privileges

class User():
	_users = {}
	def __init__(self, name):
		# important: always process the name in lowercase
		self.name = name.lower()
		self._components = {}
		self._privileges = []
		
		
	def initializeUnpickableData(self, hosts, log):
		for component in self._components.values():
			component.initializeUnpickableData(hosts, log)
	

	def __getstate__(self):
		return {
			'name': self.name,
			'_components': self._components,
			'_privileges': self._privileges
			}
		
	def __str__(self):
		return 'User [name=%s]' % self.name


	def getUniqueComponentId(self):
		return (max(self._components.keys()) if len(self._components) > 0 else 0)+1

	def getPrivileges(self):
		return self._privileges
	def hasPrivilege(self, privilege):
		return True
		return ( self._privileges & privilege ) > 0

	def delete(self, comp):
		if not isinstance(comp, Component):
			raise ValueError('Comp must be an instance of Component')

		if not self.hasComponent(comp.id):
			raise ValueError('Given component does not belong to the user [compId="%s"]' % str(comp.id))

		component = self._components[comp.id]
		# check if the component has children
		if len(component.children):
			parent = component.parent
			# set all child's parent to this component's parent
			for child in component.children:
				child.parent = parent
				# parent might be None, so check first before
				# appending the child to the parent's children
				if parent:
					parent.children.append(child)
					
		del self._components[comp.id]
			

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

	def deleteComponent(self, compId):
		compId = int(compId)
		if not self.hasComponent(compId):
			raise ValueError('User has no component with id "%d"' % compId)
			
		component = self.getComponent(compId)

		if component.isAlive():
			raise ValueError('The passed component is still alive. Stop first [id="%d"]' % compId)

		# check whether the component has a parentId. If so, remove
		# it from the child list of that component
		if component.parent:
			del component.parent.children[component.parent.children.index(component)]

		# if the component has children, set this parentId as the parentId
		# for all children
		for child in component.children:
			child.parent = component.parent
						 

		del self._components[compId]

	# return all ids i.e. keys() of components
	def getIDs(self):
		return self._components.keys()


	# used to iterate
	def iteritems(self):
		return self._components.iteritems()


	# get all items
	def components(self):
		return self._components.values()
