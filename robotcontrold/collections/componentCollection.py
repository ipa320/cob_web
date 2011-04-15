
class ComponentCollection():

	def __init__(self):
		self.components = {}


	# Key must be a list (user, compId) and value must be a Module
	def __setitem__(self, key, value):
		if not isinstance(key, tuple) and not isinstance(key, list):
			raise ValueError('Key must be a tuple or a list with 2 items (user, compId)')

		if len(key) != 2:
			raise ValueError ('Key must be a tuple or list with 2 items (user, compId)')

		if not isinstance(key[0], User) or not isinstance(key[1], int):
			raise ValueError ('Key must be a tuple or list with 2 items (user, compId)')

		if not isinstance(value, Module):
			raise ValueError ('Value must be an instance of Module')

		if not user.name in self.components:
			self.components[user.name] = {}

		self.components[user.name][
