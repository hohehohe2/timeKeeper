
# ======================================================
class Observable(object):

	def __init__(self):
		self.__observers = []

	def addObserver(self, observer):
		if observer not in self.__observers:
			self.__observers.append(observer)

	def removeObserver(self, observer):
		if observer in self.__observers:
			self.__observers.remove(observer)

	def clearObservers(self):
			self.__observers = []

	def getObservers(self):
		return self.__observers

	def _notify(self, event, data=None):
		for observer in self.__observers:
			observer._onNotify(self, event, data)

	def _onNotify(self, notifier, event, data):
		pass

# ======================================================
# Gui independent hierarchical node network model
"""
It's not worth a class to model the whole network, we can just
have MTreeNode tree and list of tuples for connections
Just like Maya, nodes and connections can be handled separately


An MTreeNode
	- has attributes
	- can be observed
	- can observe other nodes
	- can have parent-child relationship

When a node is deleted, recursively all the children are deleted beforehand

An observer should have _onNotify() method;
	_onNotify(self, notifier, event, data)

Predefined events:
	'deleted': no additional data
	'childRemoved' : data = oldChild, called when a child is *being* removed too
	'childAdded' : data = newChild
	'attrChanged' : data = (attrName, oldValue, newValue)
		oldValue==NOT_EXIST if the attribute is created

	In addition to these, a subclass can create and notify its own events
	Nodes being deleted emit 'deleted' events, and
	'childRemoved' if children exist

A node can observe itself;

	self.addObserver(self)
	...
	def _onNotify(self, notifier, event, data):
		if notifier == self and event in ['childAdded', 'childRemoved']:
			...
"""

NOT_EXIST = object()
class MTreeNode(Observable):

	def __init__(self, parent=None):
		super(MTreeNode, self).__init__()
		self.__attr = {} # {attrName: value}
		self.__parent = None
		self.__children = []

		self.setParent(parent)

	def delete(self):

		while self.__children:
			child = self.__children.pop()
			child.delete()

		if self.__parent:
			self.__parent._removeChild(self)
			self.__parent = None

		self.__attrs = {}

		self._notify('deleted')
		self.__observers = []

	def setAttr(self, name, value):
		"""
		It creates an attribute if it does not exist
		"""
		oldValue = self.__attr.get(name, NOT_EXIST)
		self.__attr[name] = value
		self._notify('attrChanged', (name, oldValue, value))

	def getAttr(self, name):
		return self.__attr[name]

	def hasAttr(self, name):
		return name in self.__attr

	def getAttrDefault(self, name, default=None):
		return self.__attr.get(name, default)

	def setParent(self, parent):
		assert(parent != self)

		oldParent = self.__parent
		if oldParent == parent:
			return

		self.__parent = parent

		if oldParent:
			oldParent._removeChild(self)
		if parent:
			parent._addChild(self)

	def getParent(self):
		return self.__parent

	def getChildren(self):
		return tuple(self.__children)

	def _removeChild(self, child):
		if child in self.__children:
			self.__children.remove(child)
		self._notify('childRemoved', child)

	def _addChild(self, child):
		if not child in self.__children:
			self.__children.append(child)
		self._notify('childAdded', child)

	def __getstate__(self):

		d = self.__dict__.copy()

		# Remove observers that may not be appropriate to be serialized eg. GUI classes
		# Also we exclude observers that are not under _serializeRoot to keep parent-child
		# relationship consistent.

		# For efficiency we just check if self is _serializeRoot and exclude if it is a root
		# expecting it prevents serializing the while MTreeNode tree through Python reference but
		# it doesn't work if we have additional MTreeNode observers outside of the tree

		observers = self.getObservers()[:]
		observers = [x for x in observers if isinstance(x, MTreeNode) and x != _serializeRoot]
		d['_Observable__observers'] = observers

		# Serialize only the subtree so that it won't pickle every hierarchy from the global root
		if d['_MTreeNode__parent'] == _serializeRoot:
			d['_MTreeNode__parent'] = None

		return d

	def __setstate__(self, d):
		self.__dict__ = d

# ======================================================
_serializeRoot = None
def serialize(mTreeNodes, root=None):
	"""
	Serialize the node tree(mTreeNodes) rooted at the given root.
	root should not be in mTreeNodes
	Observers are not pickled unless it's in the network
	"""
	global _serializeRoot
	import cPickle as pickle
	_serializeRoot = root
	try:
		return pickle.dumps(mTreeNodes)
	finally:
		_serializeRoot = None

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

# ------------------------------------------------------
class MTaskConnection(Observable):
	def __init__(self):
		super(MTaskConnection, self).__init__()

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
# class MTaskModel(object):

# 	def __init__(self):
# 		self.__theRoot = MTaskNode()
# 		self.__connections = []
# 		self.__observers = []

# 	def addObserver(self, observer):
# 		if not observer in self.__observers:
# 			self.__observers.append(observer)

# 	def removeObserver(self, observer):
# 		if observer in self.__observers:
# 			self.__observers.remove(observer)

# 	def addTaskNode(self, parent=None):
# 		if not parent:
# 			parent = self.__theRoot

# 		node = MTaskNode(parent)
# 		node.addObserver(self) # To delect deletion
# 		self.__onUpdate('task', node) # For canvas update, nodes notifies deletion by themselves

# 		return node

# 	def addTaskDotNode(self, parent):
# 		if not parent:
# 			parent = self.__theRoot

# 		node = MTaskDotNode(parent)
# 		node.addObserver(self) # To delect deletion
# 		self.__onUpdate('dot', node) # For canvas update, nodes notifies deletion by themselves

# 		return node

# 	def addConnection(self, mNodeFrom, mNodeTo):
# 		self.__connections.append((mNodeFrom, mNodeTo))
# 		self.__onUpdate('connection', node) # For canvas update

# 	def removeConnection(self, mNodeFrom, mNodeTo):
# 		self.__connections.remove((mNodeFrom, mNodeTo))
# 		self.__onUpdate('delete connection', node) # For canvas update

# 	def __onUpdate(self, kind, node):
# 		for observer in self.__observers:
# 			observer.onNofity(kind, node)

# 	def _onNotify(self, notifier, event, data):
# 		if event == 'deleted':
# 			self.__nodes.remove(notifier)

# ======================================================

if __name__ == '__main__':

	def treeNodeTest():

		class NamedMTreeNode(MTreeNode):
			def __init__(self, name):
				super(NamedMTreeNode, self).__init__()
				self.setAttr('name', name)
			def __str__(self):
				return self.getAttr('name')

		class ObservingNode(NamedMTreeNode):
			def _onNotify(self, notifier, event, data):
				print notifier.getAttr('name'), event, data	

		a = ObservingNode('a')

		b = NamedMTreeNode('b')
		c = NamedMTreeNode('c')
		d = NamedMTreeNode('d')

		b.addObserver(a)
		c.addObserver(a)
		d.addObserver(a)

		print ':setAttr'
		c.setAttr('myAttr', 1)
		print ':c.setParent(b)'
		c.setParent(b)
		print ':d.setParent(c)'
		d.setParent(c)
		print ':c.delete()'
		c.delete()

	def networkTest():

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

	treeNodeTest()
	networkTest()