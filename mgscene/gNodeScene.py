# Timekeeper GUI node

from gnode.gnode_main import GScene
from mnode.mnode_main import MNode

# ======================================================
class GNodeSceneBase(GScene):

	# {MNode subclass:GNode subclass}, used to instanciate GNodes from MNodes
	# You must provide it in the sub class.
	# GNode subclasses must have a constructor compatible with
	#	__init__(self, gScene, mNode)

	_classMapper = {}

	def __init__(self, *args, **kargs):
		super(GNodeSceneBase, self).__init__(*args, **kargs)
		self.__rootMNode = MNode()

	def resetNetwork(self, rootMNode, connections):
		"""
		Make this scene represents the network under rootMNode
		connections where either of the node is not a direct child of rootMNode are ignored
		_classMapper is used to find the appropriate GNode sub class for each mNode
		"""
		assert(isinstance(rootMNode, MNode))

		self.clear()
		self.__rootMNode = rootMNode
		self.addNetwork(rootMNode.getChildren(), connections)

	def addNetwork(self, mNodes, connections):
		"""
		Add a network to the current scene.
		MNodes which parent is not the current root are ignored
		connections where either of the node is not a direct child of current root Mnode are ignored
		_classMapper is used to find the appropriate GNode sub class for each mNode
		"""
		items = self.items()
		for mNode in mNodes:
			if mNode in items:
				continue
			if mNode.getParent() != self.__rootMNode:
				continue
			gNodeClass = self._classMapper[mNode.__class__](self, mNode)

		for connectionFrom, connectionTo in connections:
			assert(connectionFrom in mNodes)
			assert(connectionTo in mNodes)
			GConnection(connectionFrom, connectionTo)
