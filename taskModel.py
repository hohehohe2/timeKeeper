from utils.observable import Observable
from utils.treeNode import TreeNode

# ======================================================
class MTaskModel(Observable):

	def __init__(self):
		super(MTaskModel, self).__init__()
		self.__theRoot = MTaskNode()
		self.__connections = []

	def getRoot(self):
		return self.__theRoot

	def addTaskNode(self, parent):
		return self.__addNode(parent, MTaskNode, 'createTask')

	def addTaskDotNode(self, parent):
		return self.__addNode(parent, MTaskDotNode, 'createDot')

	def addTaskConnection(self, mNodeFrom, mNodeTo):
		self.__checkNode(mNodeFrom)
		assert(mNodeFrom.getParent() == mNodeTo.getParent())
		connection = MTaskConnection(mNodeFrom, mNodeTo)
		self.__connections.append(connection)
		connection.addObserver(self)
		self._notify('createConnection', connection) # For canvas update
		return connection

	def __addNode(self, parent, taskClass, eventToEmit):
		if not parent:
			parent = self.__theRoot
		else:
			self.__checkNode(parent)

		node = taskClass(parent)

		# Node can remove itself from the tree on deletion so MTaskModel does not observe nodes
		#node.addObserver(self)

		self._notify(eventToEmit, node) # For canvas update, nodes/connections notify their deletion by themselves

		return node

	def __checkNode(self, parent):
		# Check if the node is in the tree rooted at self.__theRoot
		p = parent
		while p:
			if p == self.__theRoot:
				break
			p = p.getParent()
		else:
			assert(False and "parent is not under the root")

	def _onNotify(self, notifier, event, data):
		if event == 'deleted':
			assert(notifier in self.__connections)
			self.__connections.remove(notifier)

# ------------------------------------------------------
class MTaskNode(TreeNode):
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

	def isNode(self):
		return True

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
class MTaskDotNode(TreeNode):
	def __init__(self, parent=None):
		super(MTaskDotNode, self).__init__(parent)
		self.setAttr('pos', (0, 0))

	def isNode(self):
		return True

# ------------------------------------------------------
# Connection is not a tree node so let's just inherit Observable
class MTaskConnection(Observable):
	def __init__(self, fromMNode, toMNode):
		super(MTaskConnection, self).__init__()
		self.__from = fromMNode
		self.__to = toMNode

	def getFrom(self):
		return self.__from

	def getTo(self):
		return self.__to

	def isNode(self):
		return False

	def delete(self):
		self._notify('deleted')
		self.clearObservers()

	def __getstate__(self):
		d = self.__dict__.copy()
		d['_Obserbable__observers'] = []
		return d

	def __setstate__(self, d):
		self.__dict__ = d

# ======================================================

if __name__ == '__main__':

	import cPickle as pickle

	def createNetwork():
		root = MTaskNode()
		pt1 = MTaskNode(root)
		pt2 = MTaskNode(root)
		ct1 = MTaskNode(pt1)
		ct2 = MTaskNode(pt1)
		gt1 = MTaskNode(ct2)

		from utils.treeNode import serialize
		return serialize([root, pt1, pt2, ct1, ct2, gt1])

	def nodeTest():

		pickledNetwork = createNetwork()
		root, pt1, pt2, ct1, ct2, gt1 = pickle.loads(pickledNetwork)

		ct1.setAttr('actual', 3.0)
		assert(pt1.getAttr('actual') == 3.0)
		gt1.setAttr('actual', 4.0)
		assert(pt1.getAttr('actual') == 7.0)
		ct1.delete()
		assert(pt1.getAttr('actual') == 4.0)
		gt1.setParent(None)
		assert(pt1.getAttr('actual') == 0.0)
