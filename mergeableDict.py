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

if __name__ == '__main__':
	a = MergeableDict()
	a.update({1: 10, 2: 20, 3: 30, 4: {-2: -20, -1: -10}})
	b = { 1:100, 4:{-1:-100, -4:-400}, 5:400}
	a.merge(b)
	assert(a == {1: 100, 2: 20, 3: 30, 4: {-4: -400, -1: -100, -2: -20}, 5: 400})
