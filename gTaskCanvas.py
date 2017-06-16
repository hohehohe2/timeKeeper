from Qt import QtCore
from nodeViewFramework.frameworkMain import GCanvas, GConnection
from utils.observable import Observable

from taskModel import MTaskNode, MTaskDotNode
from taskView import GTaskNode, GTaskDotNode

# ======================================================
class GTaskCanvas(GCanvas, Observable):

	def __init__(self, *args, **kargs):
		super(GTaskCanvas, self).__init__(*args, **kargs)
		Observable.__init__(self)
		self.__rootTaskNode = None

	def keyPressEvent(self, event):
		super(GTaskCanvas, self).keyPressEvent(event)

		if event.modifiers() == QtCore.Qt.ControlModifier:
			if event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
				while self.selectedItems():
					self.selectedItems()[0].delete()
			elif event.key() == QtCore.Qt.Key_N:
				self._notify('create node')
			elif event.key() == QtCore.Qt.Key_D:
				self._notify('create dot')

		self.update()

	def resetNetwork(self, rootTaskNode, connections):
		"""
		Make this canvas show the network under rootTaskNode
		connections where either of the node is not a direct child of rootTaskNode are ignored
		"""
		self.clear()
		self.__rootTaskNode = rootTaskNode
		self.addNetwork(rootTaskNode.getChildren(), connections)

	def addNetwork(self, mNodes, connections):
		"""
		Add a network to the current canvas.
		MNodes which parent is not the current root are ignored
		connections where either of the node is not a direct child of current root Mnode are ignored
		"""

		# Used to find the appropriate GNode sub class for each mNode
		classMapper = {
			MTaskNode : GTaskNode,
			MTaskDotNode : GTaskDotNode,
			}

		items = self.items()
		mNodeToGNode = {}
		for mNode in mNodes:

			if mNode in items:
				continue

			if mNode.getParent() != self.__rootTaskNode:
				continue

			gNodeClass = classMapper[mNode.__class__]
			gNode = gNodeClass(self, mNode) # instanciate GNode sub class instance for mNode

			mNodeToGNode[mNode] = gNode

		for connectionFrom, connectionTo in connections:
			assert(connectionFrom in mNodes)
			assert(connectionTo in mNodes)
			GConnection(mNodeToGNode[connectionFrom], mNodeToGNode[connectionTo])

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

		from utils.treeNode import serialize
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
