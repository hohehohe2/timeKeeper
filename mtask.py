from mnode.mnode_main import MNode

# ======================================================
# Prefix 'M' means 'Model'
class MTask(MNode):
	def __init__(self, parent=None):
		super(MTask, self).__init__(parent)
		self.setAttr('description', '') # Long description
		self.setAttr('estimated', 0) # Estimated time
		self.setAttr('actual', 0) # Actual time needed
		self.setAttr('status', 'waiting') # 'waiting', 'wip', 'done'
		self.setAttr('isCurrent', False) # True if now working on it

		# UI params
		self.setAttr('pos', (0, 0))
		self.setAttr('size', (0, 0))

		self.addObserver(self)

	def setParent(self, parent):
		oldParent = self.getParent()
		super(MTask, self).setParent(parent)
		if oldParent:
			self.removeObserver(oldParent)
		if parent:
			self.addObserver(parent)

	def onNotify(self, notifier, event, data):
		if notifier in self.getChildren() and event == 'attrChanged' and data[0] == 'actual':
			self.__updateActual()
		if notifier == self and event == 'childRemoved':
			self.__updateActual()

	def __updateActual(self):
		sumChildActuals = 0
		for child in self.getChildren():
			sumChildActuals += child.getAttr('actual')
		self.setAttr('actual', sumChildActuals)

# ------------------------------------------------------
class MDot(MNode):
	def __init__(self, parent=None):
		super(MTask, self).__init__(parent)
		self.setAttr('pos', (0, 0))

# ======================================================
if __name__ == '__main__':

	def createNetwork():
		root = MTask()
		pt1 = MTask(root)
		pt2 = MTask(root)
		ct1 = MTask(pt1)
		ct2 = MTask(pt1)
		gt1 = MTask(ct2)
		return MNode.serialize([root, pt1, pt2, ct1, ct2, gt1])

	pickledNetwork = createNetwork()
	import cPickle as pickle
	root, pt1, pt2, ct1, ct2, gt1 = pickle.loads(pickledNetwork)

	ct1.setAttr('actual', 3.0)
	assert(pt1.getAttr('actual') == 3.0)
	gt1.setAttr('actual', 4.0)
	assert(pt1.getAttr('actual') == 7.0)
	ct1.delete()
	assert(pt1.getAttr('actual') == 4.0)
	gt1.setParent(None)
	assert(pt1.getAttr('actual') == 0.0)

