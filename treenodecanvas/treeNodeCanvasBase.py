# Timekeeper GUI node

from gnode.gnode_main import GCanvas, GConnection
from treenodecanvas.treeNode import MTreeNode

# ======================================================
class GTreeNodeCanvasBase(GCanvas):

	# {MTreeNode subclass:GNode subclass}, used to instanciate GNodes from MTreeNodes
	# You must provide it in the sub class.
	# GNode subclasses must have a constructor compatible with
	#	__init__(self, gCanvas, mTreeNode)

	_classMapper = {}

	def __init__(self, *args, **kargs):
		super(GTreeNodeCanvasBase, self).__init__(*args, **kargs)
		self.__rootMTreeNode = MTreeNode()

	def resetNetwork(self, rootMTreeNode, connections):
		"""
		Make this canvas represents the network under rootMTreeNode
		connections where either of the node is not a direct child of rootMTreeNode are ignored
		_classMapper is used to find the appropriate GNode sub class for each mTreeNode
		"""
		assert(isinstance(rootMTreeNode, MTreeNode))

		self.clear()
		self.__rootMTreeNode = rootMTreeNode
		self.addNetwork(rootMTreeNode.getChildren(), connections)

	def addNetwork(self, mTreeNodes, connections):
		"""
		Add a network to the current canvas.
		MTreeNodes which parent is not the current root are ignored
		connections where either of the node is not a direct child of current root Mnode are ignored
		_classMapper is used to find the appropriate GNode sub class for each mTreeNode
		"""
		items = self.items()
		mTreeNodeToGNode = {}
		for mTreeNode in mTreeNodes:
			if mTreeNode in items:
				continue
			if mTreeNode.getParent() != self.__rootMTreeNode:
				continue
			gNodeClass = self._classMapper[mTreeNode.__class__]
			gNode = gNodeClass(self, mTreeNode) # instanciate GNode sub class instance for mTreeNode
			mTreeNodeToGNode[mTreeNode] = gNode

		for connectionFrom, connectionTo in connections:
			assert(connectionFrom in mTreeNodes)
			assert(connectionTo in mTreeNodes)
			GConnection(mTreeNodeToGNode[connectionFrom], mTreeNodeToGNode[connectionTo])
