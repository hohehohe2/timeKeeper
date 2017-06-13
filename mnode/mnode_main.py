# ======================================================
# Gui independent hierarchical node network model

class MNode(object):
	"""
	Node model.
	An MNode
		- has attributes
		- can be observed
		- can observe other nodes
		- can have parent-child relationship
	When a node is deleted, recursively all the children are deleted beforehand

	An observer should have onNotify() method;
		onNotify(self, notifier, event, data)

	Predefined events:
		'deleting': no additional data
		'deleted': no additional data
		'parentChanged' : data = (oldParent, newParent), oldParent, newParent can be None
		'childRemoved' : data = oldChild, called when a child is *being* removed too
		'childAdded' : data = newChild
		'attrChanged' : data = (attrName, oldValue, newValue)
			oldValue==MNode.NOT_EXIST if the attribute is created

		In addition to these, a subclass can create and notify its own events
		Nodes being deleted emit 'deleting' and 'deleted' events, and
		'childRemoved' if children exist

	A node can observe itself;

		self.addObserver(self)
		...
		def onNotify(self, notifier, event, data):
			if notifier == self and event in ['childAdded', 'childRemoved']:
				...
	"""

	NOT_EXIST = object()

	def __init__(self, parent=None):
		self.__attr = {} # {attrName: value}
		self.__observers = [] # List of MNodes that are observing this object
		self.__parent = None
		self.__children = []

		self.setParent(parent)

	def delete(self):
		self.notify('deleting')

		while self.__children:
			child = self.__children.pop()
			child.delete()

		if self.__parent:
			self.__parent._removeChild(self)
			self.__parent = None

		self.__attrs = {}

		self.notify('deleted')

		while self.__observers:
			observer = self.__observers.pop()
			self.removeObserver(observer)

	def setAttr(self, name, value):
		"""
		It creates an attribute if it does not exist
		"""
		oldValue = self.__attr.get(name, self.NOT_EXIST)
		self.__attr[name] = value
		self.notify('attrChanged', (name, oldValue, value))

	def getAttr(self, name):
		return self.__attr[name]

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

		self.notify('parentChanged', (oldParent, parent))

	def getParent(self):
		return self.__parent

	def getChildren(self):
		return tuple(self.__children)

	def notify(self, event, data=None):
		for observer in self.__observers:
			observer.onNotify(self, event, data)

	def _removeChild(self, child):
		if child in self.__children:
			self.__children.remove(child)
		self.notify('childRemoved', child)

	def _addChild(self, child):
		if not child in self.__children:
			self.__children.append(child)
		self.notify('childAdded', child)

if __name__ == '__main__':

	class NamedMNode(MNode):
		def __init__(self, name):
			super(NamedMNode, self).__init__()
			self.setAttr('name', name)
		def __str__(self):
			return self.getAttr('name')

	class ObservingMNode(NamedMNode):
		def onNotify(self, notifier, event, data):
			print notifier.getAttr('name'), event, data	

	a = ObservingMNode('a')

	b = NamedMNode('b')
	c = NamedMNode('c')
	d = NamedMNode('d')

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
