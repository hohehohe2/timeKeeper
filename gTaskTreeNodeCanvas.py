from gnode.gnode_main import GCanvas, GConnection

from nody_utils.treeNode import MTreeNode
from mtask import MTaskNode, MTaskDotNode
from gtask import GTaskNode, GTaskDotNode

# ======================================================
class GTaskTreeNodeCanvas(GCanvas):

	_classMapper = {
		MTaskNode : GTaskNode,
		MTaskDotNode : GTaskDotNode,
		}

	def __init__(self, *args, **kargs):
		super(GTaskTreeNodeCanvas, self).__init__(*args, **kargs)
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

	global app, view

	app = QtWidgets.QApplication(sys.argv)

	canvas = GTaskTreeNodeCanvas()

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
