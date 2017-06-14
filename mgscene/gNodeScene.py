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
		super(GNodeScene, self).__init__(*args, **kargs)
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
			if not mNode.getParent() != self.__rootMNode:
				continue
			gNodeClass = self._classMapper[mNode.__class]()

		for connectionFrom, connectionTo in connections:
			assert(connectionFrom in mNodes)
			assert(connectionTo in mNodes)
			GConnection(connectionFrom, connectionTo)


# # ======================================================
# if __name__ == '__main__':
# 	def createNetwork():

# 		root = MTaskNode()
# 		pt1 = MTaskNode(root)
# 		pt2 = MTaskNode(root)
# 		ct1 = MTaskNode(pt1)
# 		ct2 = MTaskNode(pt1)
# 		gt1 = MTaskNode(ct2)

# 		pt1.setAttr('pos', (0, 60))
# 		pt2.setAttr('pos', (170, 60))
# 		ct1.setAttr('pos', (0, 120))
# 		ct2.setAttr('pos', (170, 120))
# 		gt1.setAttr('pos', (170, 180))

# 		ct1.setAttr('actual', 3.0)
# 		gt1.setAttr('actual', 4.0)

# 		from mnode.mnode_main import serialize
# 		return serialize([root, pt1, pt2, ct1, ct2, gt1])

# 	global app, view

# 	import sys
# 	app = QtWidgets.QApplication(sys.argv)

# 	scene = GNodeScene()
# 	view = GView(None, scene)

# 	pickledNetwork = createNetwork()
# 	import cPickle as pickle
# 	network = pickle.loads(pickledNetwork)
# 	root = network[0]

# 	scene.resetNetwork(root, ())
# 	scene.addNetwork(network, ())

# 	view.show()
# 	app.exec_()
