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

class DynamicMergeableDict(dict):
	"""
	Works the same way as MergeableDict dynamically but very slow!
	Only d.get() and d[key] behavior are overriden
	Note that key in d doesn't take the base into account
	"""

	def __init__(self, *args, **kargs):
		super(DynamicMergeableDict, self).__init__(*args, **kargs)
		self.__base = {}

	def setBase(self, baseDict):
		self.__base = baseDict

	def get(self, key, default=None):
		try:
			return self[key]
		except KeyError:
			return default

	def __getitem__(self, key):
		notFound = object()

		selfResult = super(DynamicMergeableDict, self).get(key, notFound)

		if selfResult == notFound:
			return self.__base[key]

		if not isinstance(selfResult, dict):
			return selfResult

		baseResult = self.__base.get(key)

		if not isinstance(baseResult, dict):
			return selfResult

		dSelfResult = DynamicMergeableDict()
		dSelfResult.update(selfResult)
		dBaseResult = DynamicMergeableDict()
		dBaseResult.update(baseResult)
		dSelfResult.setBase(dBaseResult)

		return dSelfResult

if __name__ == '__main__':
	base = {1:1, 2:2, 3:{31:31, 32:32, 33:{331:331, 332:332}}}
	over = {2:-2, 4:-4, 3:{32:-32, 34:-34, 33:{332:-332, 334:-334}}}
	expected = {1:1, 2:-2, 4:-4, 3:{31:31, 32:-32, 34:-34, 33:{331:331, 332:-332, 334:-334}}}

	a = MergeableDict()
	a.update(base)
	a.merge(over)
	assert(a == expected)

	b = DynamicMergeableDict()
	b.update(over)
	b.setBase(base)
	assert[b[1] == 1]
	assert[b[2] == -2]
	assert[b[4] == -4]
	assert[b[3][31] == 31]
	assert[b[3][32] == -32]
	assert[b[3][34] == -34]
	assert[b[3][33][331] == 331]
	assert[b[3][33][332] == -332]
	assert[b[3][33][334] == -334]
