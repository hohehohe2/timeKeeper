from Qt import QtCore, QtGui
from nodeViewFramework.frameworkMain import GCanvas, GConnection

from taskModel import MTaskNode, MTaskDotNode
from taskView import GTaskNode, GTaskDotNode

# ======================================================
class GTaskCanvas(GCanvas):

	def __init__(self, mTaskModel, rootMTaskNode=None, *args, **kargs):
		super(GTaskCanvas, self).__init__(*args, **kargs)
		self.__mTaskModel = mTaskModel
		mTaskModel.addObserver(self)

		if rootMTaskNode:
			self.__rootMTaskNode = rootMTaskNode
		else:
			self.__rootMTaskNode = mTaskModel.getRoot()

	def keyPressEvent(self, event):
		super(GTaskCanvas, self).keyPressEvent(event)
		view = self.views()[0]
		pos = view.mapToScene(view.mapFromGlobal(QtGui.QCursor.pos()))
		pos = pos.x(), pos.y()

		if event.modifiers() == QtCore.Qt.ControlModifier:
			if event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
				while self.selectedItems():
					self.selectedItems()[0].delete()
			elif event.key() == QtCore.Qt.Key_N:
				node = self.__mTaskModel.addTaskNode(self.__rootMTaskNode)
				node.setAttr('pos', pos)
			elif event.key() == QtCore.Qt.Key_D:
				node = self.__mTaskModel.addTaskDotNode(self.__rootMTaskNode)
				node.setAttr('pos', pos)

		self.update()

	def resetNetwork(self, rootMTaskNode, connections):
		"""
		Make this canvas show the network under rootTaskNode
		connections where either of the node is not a direct child of rootTaskNode are ignored
		"""
		self.clear()
		self.__rootMTaskNode = rootMTaskNode
		self._addNetwork(rootMTaskNode.getChildren(), connections)

	def _addNetwork(self, mNodes, connections):
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

			assert(mNode.getParent() == self.__rootMTaskNode)

			gNodeClass = classMapper[mNode.__class__]
			gNode = gNodeClass(self, mNode) # instanciate GNode sub class instance for mNode

			mNodeToGNode[mNode] = gNode

		for connection in connections:
			assert(connection.getFrom() in mNodes)
			assert(connection.getTo() in mNodes)
			GConnection(mNodeToGNode[connection.getFrom()], mNodeToGNode[connection.getTo()])

	def _onNotify(self, notifier, event, data):
		if event in ['createTask', 'createDot']:
			self._addNetwork([data], ())

# ======================================================
if __name__ == '__main__':
	import sys
	from Qt import QtWidgets
	from taskModel import MTaskModel, MTaskConnection

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

	model = MTaskModel()
	canvas = GTaskCanvas(model)
	canvas2 = GTaskCanvas(model)

	pickledNetwork = createNetwork()
	import cPickle as pickle
	root, pt1, pt2, ct1, ct2, gt1 = pickle.loads(pickledNetwork)

	#canvas.resetNetwork(root, ())

	ct1.setParent(model.getRoot())
	ct2.setParent(model.getRoot())
	connections = (MTaskConnection(ct1, ct2),)
	canvas._addNetwork([ct1, ct2], connections) # Temporal, call model.addNode(), addConnection() etc.
	canvas2._addNetwork([ct1, ct2], connections)

	canvas.show()
	canvas2.show()
	app.exec_()
