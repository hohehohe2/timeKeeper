"""
This module offers a couple of silly dict sub classes
"""

class MergeableDict(dict):
	def merge(self, other):
		"""
		Works similarly to someDict.update(otherDict) but dict values are merged recursively,
		not just replaced
		"""
		assert(isinstance(other, dict))
		MergeableDict.__merge(self, other)

	@staticmethod
	def __merge(this, other):

		for key, ovalue in other.items():

			if key not in this:
				this[key] = ovalue
				continue

			svalue = this[key]

			if isinstance(ovalue, dict) and isinstance(svalue, dict):
				MergeableDict.__merge(svalue, ovalue)
			else:
				this[key] = ovalue

class InheritableDict(dict):
	"""
	Only d.get() and d[key] behavior are overriden
	"""

	def __init__(self, *args, **kargs):
		super(InheritableDict, self).__init__(*args, **kargs)
		self.__base = {}

	def setBase(self, baseDict):
		self.__base = baseDict

	def contains(self, item):
		return super(InheritableDict, self).__contains__(item) or item in self.__base

	def get(self, key, default=None):
		try:
			return self[key]
		except:
			return default

	def __getitem__(self, key):
		if super(InheritableDict, self).__contains__(key):
			return super(InheritableDict, self).__getitem__(key)
		return self.__base[key]

if __name__ == '__main__':
	a = MergeableDict()
	a.update({1: 10, 2: 20, 3: 30, 4: {-2: -20, -1: -10}})
	b = { 1:100, 4:{-1:-100, -4:-400}, 5:400}
	a.merge(b)
	assert(a == {1: 100, 2: 20, 3: 30, 4: {-4: -400, -1: -100, -2: -20}, 5: 400})

	x = dict(a=10, b=20)
	y = InheritableDict(b=200, c=300)
	y.setBase(x)
	assert('a' not in y)
	assert('b' in y)
	assert(y.contains('a')) # 'a' in y equivalent that takes the base into account
	assert(y.contains('b'))
	assert(y['b'] == 200)
	assert(y['c'] == 300)
	assert(y['a'] == 10)
	assert(y.get('b') == 200)
	assert(y.get('c') == 300)
	assert(y.get('a') == 10)
	assert(y.get('d') == None)
