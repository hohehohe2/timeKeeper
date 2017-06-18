from Qt import QtCore, QtGui
from nodeViewFramework.frameworkMain import GCanvas, GConnection

from taskModel import MTaskNode, MTaskDotNode
from taskView import GTaskNode, GTaskDotNode, GTaskConnection

# ======================================================
class GTaskCanvas(GCanvas):
	"""
	Kind of ad-hoc canvas class for timeKeeper application
	"""

	def __init__(self, mTaskModel, rootMTaskNode=None, *args, **kargs):
		super(GTaskCanvas, self).__init__(*args, **kargs)
		self.__mTaskModel = mTaskModel
		mTaskModel.addObserver(self) # Observe mTask to receive node and connection creation event.

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
			elif event.key() == QtCore.Qt.Key_C:
				gNodeFrom, gNodeTo = self.selectedItems() # TODO: selectedItems() has no order
				print self.selectedItems()
				self.__mTaskModel.addTaskConnection(gNodeFrom.getMItem(), gNodeTo.getMItem())


		self.update()

	def resetNetwork(self, rootMTaskNode, connections):
		"""
		Make this canvas show the network under rootTaskNode
		connections where either of the node is not a direct child of rootTaskNode are ignored
		"""
		self.clear()
		self.__rootMTaskNode = rootMTaskNode
		self._addNetwork(rootMTaskNode.getChildren(), connections)

	def _addNetwork(self, mNodes, mConnections):
		"""
		Add a network to the current canvas.
		MNodes which parent is not the current root are ignored
		connections where either of the node is not a direct child of current root Mnode are ignored
		"""

		mToGMapND, mToGMapC = self.__getMItemToGItemMap()

		# Used to find the appropriate GNode sub class for each mNode
		classMapper = {
			MTaskNode : GTaskNode,
			MTaskDotNode : GTaskDotNode,
			}

		for mNode in mNodes:

			if mNode.getParent() != self.__rootMTaskNode:
				continue

			gNode = mToGMapND.get(mNode)
			if gNode:
				continue # Already exists

			gNodeClass = classMapper[mNode.__class__]
			gNode = gNodeClass(self, mNode) # instanciate GNode sub class instance for the mNode

			mToGMapND[mNode] = gNode

		for mConnection in mConnections:
			mNodeFrom = mConnection.getFrom()
			mNodeTo = mConnection.getTo()
			assert(mNodeFrom.getParent() == mNodeTo.getParent())

			if mNodeFrom.getParent() != self.__rootMTaskNode:
				continue

			gNodeFrom = mToGMapND.get(mNodeFrom)
			gNodeTo = mToGMapND.get(mNodeTo)

			assert(gNodeFrom and gNodeTo)

			GTaskConnection(self, mConnection) # instanciate GConnection sub class instance for the mConnection

	def __getMItemToGItemMap(self):

		def createMap(gItemClass):
			gItems = [x for x in self.items() if isinstance(x, gItemClass)]
			gToMList = [(x.getMItem(), x) for x in gItems]
			return dict(gToMList)

		mToGMapND = createMap(GTaskNode)
		mToGMapND.update(createMap(GTaskDotNode))
		mToGMapC = createMap(GConnection)

		return mToGMapND, mToGMapC

	def _onNotify(self, notifier, event, data):
		if event in ['createTask', 'createDot']:
			self._addNetwork([data], ())
		elif event == 'createConnection':
			self._addNetwork([], (data,))

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
