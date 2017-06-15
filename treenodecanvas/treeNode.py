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
	'deleting': no additional data
	'deleted': no additional data
	'parentChanged' : data = (oldParent, newParent), oldParent, newParent can be None
	'childRemoved' : data = oldChild, called when a child is *being* removed too
	'childAdded' : data = newChild
	'attrChanged' : data = (attrName, oldValue, newValue)
		oldValue==NOT_EXIST if the attribute is created

	In addition to these, a subclass can create and notify its own events
	Nodes being deleted emit 'deleting' and 'deleted' events, and
	'childRemoved' if children exist

A node can observe itself;

	self.addObserver(self)
	...
	def _onNotify(self, notifier, event, data):
		if notifier == self and event in ['childAdded', 'childRemoved']:
			...
"""

NOT_EXIST = object()
class MTreeNode(object):

	def __init__(self, parent=None):
		self.__attr = {} # {attrName: value}
		self.__observers = [] # List of MTreeNodes that are observing this object
		self.__parent = None
		self.__children = []

		self.setParent(parent)

	def delete(self):
		self._notify('deleting')

		while self.__children:
			child = self.__children.pop()
			child.delete()

		if self.__parent:
			self.__parent._removeChild(self)
			self.__parent = None

		self.__attrs = {}

		self._notify('deleted')

		while self.__observers:
			observer = self.__observers.pop()
			self.removeObserver(observer)

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

	def addObserver(self, observer):
		if observer not in self.__observers:
			self.__observers.append(observer)

	def removeObserver(self, observer):
		if observer in self.__observers:
			self.__observers.remove(observer)

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

		self._notify('parentChanged', (oldParent, parent))

	def getParent(self):
		return self.__parent

	def getChildren(self):
		return tuple(self.__children)

	def _notify(self, event, data=None):
		for observer in self.__observers:
			observer._onNotify(self, event, data)

	def _removeChild(self, child):
		if child in self.__children:
			self.__children.remove(child)
		self._notify('childRemoved', child)

	def _addChild(self, child):
		if not child in self.__children:
			self.__children.append(child)
		self._notify('childAdded', child)

	def __getstate__(self):
		privatePrefix = '_MTreeNode'

		d = self.__dict__.copy()

		# Remove observers that may not be appropriate to be serialized eg. GUI classes
		# Also we exclude observers that are not under _serializeRoot to keep parent-child
		# relationship consistent.

		# For efficiency we just check if self is _serializeRoot and exclude if it is a root
		# expecting it prevents serializing the while MTreeNode tree through Python reference but
		# it doesn't work if we have additional MTreeNode observers outside of the tree
		def excludeNonNetwork(candidates, attrName):
			candCopy = candidates[:]
			candCopy = [x for x in candCopy if isinstance(x, MTreeNode) and x != _serializeRoot]
			d[privatePrefix + attrName] = candCopy

		excludeNonNetwork(self.__observers, '__observers')

		# Serialize only the subtree so that it won't pickle every hierarchy from the global root
		if d[privatePrefix + '__parent'] == _serializeRoot:
			d[privatePrefix + '__parent'] = None
		return d

	def __setstate__(self, d):
		self.__dict__ = d

	def _onNotify(self, notifier, event, data):
		pass

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

# ======================================================
if __name__ == '__main__':

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
