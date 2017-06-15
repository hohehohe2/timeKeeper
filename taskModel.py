from nody_utils.treeNode import MTreeNode

# ======================================================
class MTaskModel(object):

	def __init__(self):
		self.__theRoot = MTaskNode()
		self.__connections = []
		self.__observers = []

	def addObserver(self, observer):
		if not observer in self.__observers:
			self.__observers.append(observer)

	def removeObserver(self, observer):
		if observer in self.__observers:
			self.__observers.remove(observer)

	def addTaskNode(self, parent=None):
		if not parent:
			parent = self.__theRoot

		node = MTaskNode(parent)
		node.addObserver(self) # To delect deletion
		self.__onUpdate('task', node) # For canvas update, nodes notifies deletion by themselves

		return node

	def addTaskDotNode(self, parent):
		if not parent:
			parent = self.__theRoot

		node = MTaskDotNode(parent)
		node.addObserver(self) # To delect deletion
		self.__onUpdate('dot', node) # For canvas update, nodes notifies deletion by themselves

		return node

	def addConnection(self, mNodeFrom, mNodeTo):
		self.__connections.append((mNodeFrom, mNodeTo))
		self.__onUpdate('connection', node) # For canvas update

	def removeConnection(self, mNodeFrom, mNodeTo):
		self.__connections.remove((mNodeFrom, mNodeTo))
		self.__onUpdate('delete connection', node) # For canvas update

	def __onUpdate(self, kind, node):
		for observer in self.__observers:
			observer.onNofity(kind, node)

	def _onNotify(self, notifier, event, data):
		if event == 'deleted':
			self.__nodes.remove(notifier)

# ------------------------------------------------------
class MTaskNode(MTreeNode):
	def __init__(self, parent=None):
		super(MTaskNode, self).__init__(parent)
		self.setAttr('description', '') # Long description
		self.setAttr('estimated', 0) # Estimated time
		self.setAttr('actual', 0) # Actual time needed
		self.setAttr('status', 'waiting') # 'waiting', 'wip', 'done'
		self.setAttr('isCurrent', False) # True if now working on it

		self.setAttr('pos', (0, 0))
		self.setAttr('size', (0, 0))

		self.addObserver(self)

	def setParent(self, parent):
		oldParent = self.getParent()
		super(MTaskNode, self).setParent(parent)
		if oldParent:
			self.removeObserver(oldParent)
		if parent:
			self.addObserver(parent)

	def _onNotify(self, notifier, event, data):
		if notifier in self.getChildren() and event == 'attrChanged' and data[0] == 'actual':
			self.__updateActual()
		if notifier == self and event == 'childRemoved':
			self.__updateActual()

	def __updateActual(self):
		sumChildActuals = 0
		for child in self.getChildren():
			if child.hasAttr('actual'):
				sumChildActuals += child.getAttr('actual')
		self.setAttr('actual', sumChildActuals)

# ------------------------------------------------------
class MTaskDotNode(MTreeNode):
	def __init__(self, parent=None):
		super(MTaskDotNode, self).__init__(parent)
		self.setAttr('pos', (0, 0))

# ======================================================
if __name__ == '__main__':

	def createNetwork():
		root = MTaskNode()
		pt1 = MTaskNode(root)
		pt2 = MTaskNode(root)
		ct1 = MTaskNode(pt1)
		ct2 = MTaskNode(pt1)
		gt1 = MTaskNode(ct2)

		from nody_utils.treeNode import serialize
		return serialize([root, pt1, pt2, ct1, ct2, gt1])

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

