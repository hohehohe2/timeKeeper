from gnode.gnode_main import GCanvas, GConnection

from taskModel import MTaskNode, MTaskDotNode
from taskGNodes import GTaskNode, GTaskDotNode

# ======================================================
class GTaskCanvas(GCanvas):

	def __init__(self, *args, **kargs):
		super(GTaskCanvas, self).__init__(*args, **kargs)
		self.__rootTaskNode = MTaskNode()

	def resetNetwork(self, rootTaskNode, connections):
		"""
		Make this canvas show the network under rootTaskNode
		connections where either of the node is not a direct child of rootTaskNode are ignored
		"""
		self.clear()
		self.__rootTaskNode = rootTaskNode
		self.addNetwork(rootTaskNode.getChildren(), connections)

	def addNetwork(self, mTreeNodes, connections):
		"""
		Add a network to the current canvas.
		MTreeNodes which parent is not the current root are ignored
		connections where either of the node is not a direct child of current root Mnode are ignored
		"""

		# Used to find the appropriate GNode sub class for each mTreeNode
		classMapper = {
			MTaskNode : GTaskNode,
			MTaskDotNode : GTaskDotNode,
			}

		items = self.items()
		mTreeNodeToGNode = {}
		for mTreeNode in mTreeNodes:

			if mTreeNode in items:
				continue

			if mTreeNode.getParent() != self.__rootTaskNode:
				continue

			gNodeClass = classMapper[mTreeNode.__class__]
			gNode = gNodeClass(self, mTreeNode) # instanciate GNode sub class instance for mTreeNode

			mTreeNodeToGNode[mTreeNode] = gNode

		for connectionFrom, connectionTo in connections:
			assert(connectionFrom in mTreeNodes)
			assert(connectionTo in mTreeNodes)
			GConnection(mTreeNodeToGNode[connectionFrom], mTreeNodeToGNode[connectionTo])

# ======================================================
if __name__ == '__main__':
	import sys
	from Qt import QtWidgets

	def createNetwork():

		root = MTaskNode()
		pt1 = MTaskNode(root)
		pt2 = MTaskNode(root)
		ct1 = MTaskNode(pt1)
		ct2 = MTaskNode(pt1)
		gt1 = MTaskNode(ct2)

		pt1.setAttr('pos', (0, 60))
		pt2.setAttr('pos', (170, 60))
		ct1.setAttr('pos', (0, 120))
		ct2.setAttr('pos', (170, 120))
		gt1.setAttr('pos', (170, 180))

		ct1.setAttr('actual', 3.0)
		gt1.setAttr('actual', 4.0)

		from nody_utils.treeNode import serialize
		return serialize([root, pt1, pt2, ct1, ct2, gt1])

	global app

	app = QtWidgets.QApplication(sys.argv)

	canvas = GTaskCanvas()

	pickledNetwork = createNetwork()
	import cPickle as pickle
	root, pt1, pt2, ct1, ct2, gt1 = pickle.loads(pickledNetwork)

	canvas.resetNetwork(root, ())

	ct1.setParent(root)
	ct2.setParent(root)
	connections = ((ct1, ct2),)
	canvas.addNetwork([ct1, ct2], connections)

	canvas.show()
	app.exec_()
