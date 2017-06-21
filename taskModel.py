import cPickle as pickle
from utils.observable import Observable
from utils.treeNode import TreeNode

# ======================================================
class MTaskModel(Observable):

	def __init__(self):
		super(MTaskModel, self).__init__()
		self.__theRoot = MTaskNode()
		self.__connections = []

		self.__pasteData = None # pickle of ([mNode], [mConnection])

	def getRoot(self):
		return self.__theRoot

	def getConnections(self, limitUnderThisChildren=None):
		if limitUnderThisChildren:
			connections = []
			for connection in self.__connections:
				if connection.getFrom().getParent() == limitUnderThisChildren:
					connections.append(connection)
			return connections
		else:
			return self.__connections

	def clear(self):
		for node in self.__theRoot.getChildren():
			node.delete()
		assert(not self.__connections)

	def save(self, filePath):
		with open(filePath, 'wb') as f:
			pickle.dump((self.__theRoot, self.__connections), f)

	def load(self, filePath):
		with open(filePath) as f:
			theRoot, connections = pickle.load(f)
		self.__theRoot = theRoot
		self.__connections = connections
		self.__observe([theRoot], connections)
		self._notify('changeRoot')

	def copy(self, mNodes):
		connections = []

		for connection in self.getConnections():
			if connection.getFrom() in mNodes and connection.getTo() in mNodes:
				connections.append(connection)

		self.__pasteData = pickle.dumps((mNodes, connections))

	def paste(self, parent):
		self.__checkNode(parent)

		nodes, connections = pickle.loads(self.__pasteData)

		for node in nodes:
			node.setParent(parent)
			if isinstance(node, MTaskNode):
				self._notify('createTask', node)
			elif isinstance(node, MTaskDotNode):
				self._notify('createDot', node)

		for connection in connections:
			self.__connections.append(connection)
			self._notify('createConnection', connection)

		for node in nodes:
			if isinstance(node, MTaskNode):
				self.assignUniqueName(node, node.getName())

		self.__observe(nodes, connections)

		return nodes, connections

	def __observe(self, nodes, connections):

		def observeNode(node):
			if not isinstance(node, MTaskNode):
				return
			if not self in node.getObservers():
				node.addObserver(self)
			for child in node.getChildren():
				observeNode(child)

		for node in nodes:
			observeNode(node)

		for connection in connections:
			if not self in connection.getObservers():
				connection.addObserver(self)

	def createTaskNode(self, parent):
		node = self.__createNode(parent, MTaskNode, 'createTask')
		self.assignUniqueName(node)
		node.addObserver(self)
		return node

	def createTaskDotNode(self, parent):
		return self.__createNode(parent, MTaskDotNode, 'createDot')

	def createTaskConnection(self, mNodeFrom, mNodeTo):
		"""
		Create connection and return it.
		Returns None if the connection already exists
		"""
		self.__checkNode(mNodeFrom)
		assert(mNodeFrom.getParent() == mNodeTo.getParent())

		for connection in self.__connections:
			if connection.getFrom() == mNodeFrom and connection.getTo() == mNodeTo:
				return None
			if connection.getFrom() == mNodeTo and connection.getTo() == mNodeFrom:
				return None

		connection = MTaskConnection(mNodeFrom, mNodeTo)
		self.__connections.append(connection)
		connection.addObserver(self)
		self._notify('createConnection', connection) # For canvas update
		return connection

	def __createNode(self, parent, taskClass, eventToEmit):
		node = taskClass(parent)
		return self.__addNode(parent, node, eventToEmit)

	def __addNode(self, parent, node, eventToEmit):
		if not parent:
			parent = self.__theRoot
		else:
			self.__checkNode(parent)

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
		if event == 'attrChanged':
			attrName, oldValue, newValue = data
			if attrName == 'name':
				assert(isinstance(notifier, MTaskNode))
				self._notify('renameTaskNode', notifier) # For canvas update
		if event == 'deleted':
			if notifier in self.__connections:
				self.__connections.remove(notifier)
			else:
				assert(isinstance(notifier, MTaskNode))
				self._notify('deleteTaskNode', notifier) # For canvas update

	@staticmethod
	def assignUniqueName(node, prefix=None):
		parent = node.getParent()
		if not parent:
			return '' # Root node name is ''

		existingNames = [x.getName() for x in parent.getChildren() if isinstance(x, MTaskNode)]

		if prefix and prefix not in existingNames:
			node.setName(prefix)
			return

		counter = 0
		if prefix:
			while prefix[-1].isdigit():
				prefix = prefix[:-1]
		if not prefix:
			prefix = 'task'

		while prefix + str(counter) in existingNames:
			counter += 1

		newName = prefix + str(counter)
		node.setName(newName)

# ------------------------------------------------------
class MTaskNode(TreeNode):
	def __init__(self, parent=None, name=''):
		super(MTaskNode, self).__init__(parent)
		self.setAttr('name', name) # Node name
		self.setAttr('description', '') # Long description
		self.setAttr('estimated', 0) # Estimated time
		self.setAttr('actual', 0) # Actual time needed
		self.setAttr('status', 'waiting') # 'waiting', 'wip', 'done'

		self.setAttr('pos', (0, 0))
		self.setAttr('size', (0, 0))

		self.addObserver(self)

	def setName(self, name):
		return self.setAttr('name', name)

	def getName(self):
		return self.getAttr('name')

	def getPathStr(self):
		parent = self.getParent()
		parentPath = parent.getPathStr() if parent else ''
		if parentPath != '/':
			parentPath += '/'
		return parentPath + self.getName()

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
		if notifier == self and (event == 'childRemoved' or event == 'childAdded'):
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
		d['_Observable__observers'] = []
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
