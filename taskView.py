# Timekeeper GUI node

from Qt import QtCore, QtGui, QtWidgets, QtCompat
from utils.mergeableDict import DynamicMergeableDict
from nodeViewFramework.paintStyle import PaintStyle
from nodeViewFramework.frameworkMain import GCanvas, GRectNode, GDotNode, GConnection
from taskModel import MTaskNode, MTaskDotNode

# ======================================================
class GTaskCanvas(GCanvas):
	"""
	Kind of ad-hoc canvas class for timeKeeper application
	"""

	def __init__(self, mTaskModel, rootMTaskNode=None, *args, **kargs):
		super(GTaskCanvas, self).__init__(*args, **kargs)
		self.__mTaskModel = mTaskModel
		mTaskModel.addObserver(self) # Observe mTask to receive node and connection creation event.
		view = self.views()[0]
		view.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		view.destroyed.connect(self.__onDestroyed)

		if rootMTaskNode:
			self.__rootMTaskNode = rootMTaskNode
		else:
			self.__rootMTaskNode = mTaskModel.getRoot()

		self.__userSpecifiedPath = self.__rootMTaskNode.getPathStr()

		view.resize(1000, 600)

	def drawBackground(self, painter, rect):
		pathStr = self.__rootMTaskNode.getPathStr()
		font = QtGui.QFont()
		pen = QtGui.QPen()
		pen.setColor(QtGui.QColor(200, 200, 200, 255))
		painter.setPen(pen)
		font.setPointSize(25)
		painter.setFont(font)
		painter.drawText(rect, pathStr)

	def keyPressEvent(self, event):
		super(GTaskCanvas, self).keyPressEvent(event)
		view = self.views()[0]
		sPos = view.mapToScene(view.mapFromGlobal(QtGui.QCursor.pos()))
		pos = sPos.x(), sPos.y()

		if event.modifiers() == QtCore.Qt.ControlModifier:
			if event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
				self.__deleteSelected()
			elif event.key() == QtCore.Qt.Key_N: # Node
				node = self.__mTaskModel.createTaskNode(self.__rootMTaskNode)
				node.setAttr('pos', pos)
			elif event.key() == QtCore.Qt.Key_D: # Dot
				node = self.__mTaskModel.createTaskDotNode(self.__rootMTaskNode)
				node.setAttr('pos', pos)
			elif event.key() == QtCore.Qt.Key_U: # Up
				if self.__rootMTaskNode.getParent():
					self.__resetNetwork(self.__rootMTaskNode.getParent())
					self.__userSpecifiedPath = self.__rootMTaskNode.getPathStr()
			elif event.key() == QtCore.Qt.Key_S: # Save
				filePath = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', filter=("time keeper (*.tkpickle)"))
				if filePath[0]:
					self.__mTaskModel.save(filePath[0])
			elif event.key() == QtCore.Qt.Key_O: # Open
				filePath = QtWidgets.QFileDialog.getOpenFileName(None, 'Open file', filter=("TimeKeeper (*.tkpickle)"))
				if filePath[0]:
					self.__mTaskModel.load(filePath[0])
					pathNode = self.__getPathNode(self.__userSpecifiedPath)
					if pathNode:
						self.__resetNetwork(pathNode)
			elif event.key() == QtCore.Qt.Key_X: # Cut
				item = self.itemAt(sPos.toPoint(), QtGui.QTransform())
				if item and item.parent():
					super(GTaskCanvas, self).keyPressEvent(event)
				else:
					self.__copySelected()
					self.__deleteSelected()
			elif event.key() == QtCore.Qt.Key_C: # Copy
				item = self.itemAt(sPos.toPoint(), QtGui.QTransform())
				if item and item.parent():
					super(GTaskCanvas, self).keyPressEvent(event)
				else:
					self.__copySelected()
			elif event.key() == QtCore.Qt.Key_V: # Paste
				item = self.itemAt(sPos.toPoint(), QtGui.QTransform())
				if item and item.parent():
					super(GTaskCanvas, self).keyPressEvent(event)
				else:
					mNodes, mConnections = self.__mTaskModel.paste(self.__rootMTaskNode)
					self.clearSelection()
					mToGMapND, mToGMapC = self.__getMItemToGItemMap()
					for mNode in mNodes:
						gNode = mToGMapND.get(mNode)
						if gNode:
							gNode.setSelected(True)
					for mConnection in mConnections:
						gConnection = mToGMapC.get(mConnection)
						if gConnection:
							gConnection.setSelected(True)
			elif event.key() == QtCore.Qt.Key_W: # Window
				newCanvas = GTaskCanvas(self.__mTaskModel, self.__rootMTaskNode)
				newCanvas.show()
				newCanvas.__resetNetwork(self.__rootMTaskNode)
				self.__userSpecifiedPath = self.__rootMTaskNode.getPathStr()
			elif event.key() == QtCore.Qt.Key_T: # Toggle status
				gNode = self._findNodeAtPosition(QtCore.QPointF(*pos))
				if not gNode:
					return
				mNode = gNode.getMItem()
				if isinstance(mNode, MTaskNode):
					status = mNode.getAttr('status')
					newStatus = {
						'waiting' : 'wip',
						'wip' : 'done',
						'done' : 'waiting',
					}[status]
					mNode.setAttr('status', newStatus)
			elif event.key() == QtCore.Qt.Key_R: # Rename
				gNode = self._findNodeAtPosition(QtCore.QPointF(*pos))
				if not gNode:
					return

				newName, isOk = QtWidgets.QInputDialog.getText(
					None,
					'Rename node',
					"New name:", QtWidgets.QLineEdit.Normal,
					'task')
				if not isOk:
					return

				self.__mTaskModel.assignUniqueName(gNode.getMItem(), newName)

		self.update()

	def __deleteSelected(self):
		while self.selectedItems():
			self.selectedItems()[0].delete()

	def __copySelected(self):
		selectedItems = self.selectedItems()
		selectedItems = [x.getMItem() for x in selectedItems]
		selectedNodes = [x for x in selectedItems if isinstance(x, (MTaskNode, MTaskDotNode))]
		self.__mTaskModel.copy(selectedNodes)

	def mouseDoubleClickEvent(self, event):
		itemFrom = self.itemAt(event.scenePos().toPoint(), QtGui.QTransform())
		if isinstance(itemFrom, GTaskNode):
			self.__resetNetwork(itemFrom.getMItem());
			self.__userSpecifiedPath = self.__rootMTaskNode.getPathStr()

	def __resetNetwork(self, rootMTaskNode=None):
		"""
		Make this canvas show the network under rootTaskNode
		"""
		self.clear()

		if rootMTaskNode:
			p = rootMTaskNode
			while p:
				if p == self.__mTaskModel.getRoot():
					break
				p = p.getParent()
			else:
				assert(False and 'Invalid root model specified')
		else:
			rootMTaskNode = self.__mTaskModel.getRoot()

		self.__rootMTaskNode = rootMTaskNode
		connections = self.__mTaskModel.getConnections(rootMTaskNode)
		self.__addNetwork(rootMTaskNode.getChildren(), connections)

		self.update()

	def __jumpTopath(self, path='/'):
		node = self.__getPathNode(path)
		if node:
			return self.__resetNetwork(node)
		else:
			return self.__resetNetwork()

	def __getPathNode(self, path):
		node = self.__mTaskModel.getRoot()
		if path == '/':
			return node

		spPath = path.split('/')[1:]
		while spPath:
			nodeName = spPath.pop(0)
			node = node.getChild(nodeName)
			if not node:
				return None # Couldn't find

		return node


	def __addNetwork(self, mNodes, mConnections):
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

			if (not mNodeFrom.getParent()) or (not mNodeTo.getParent()):
				# The connection is about to be deleted
				continue

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
			self.__addNetwork([data], ())
		elif event == 'createConnection':
			self.__addNetwork([], (data,))
		elif event == 'deleteTaskNode':
			if data == self.__rootMTaskNode:
				self.__resetNetwork()
		elif event == 'changeRoot':
			self.__jumpTopath(self.__userSpecifiedPath)
		elif event == 'renameTaskNode':
			pathNode = self.__getPathNode(self.__userSpecifiedPath)
			self.update()
			if pathNode:
				self.__userSpecifiedPath = pathNode.getPathStr()

	def _createConnection(self, gNodeFrom, gNodeTo):
		connectableNodeType = (GTaskNode, GTaskDotNode)
		if isinstance(gNodeFrom, connectableNodeType) and isinstance(gNodeTo, connectableNodeType):
			self.__mTaskModel.createTaskConnection(gNodeFrom.getMItem(), gNodeTo.getMItem())

	def __onDestroyed(self):
		self.__mTaskModel.removeObserver(self)

	def _onTaskNodeDeleted(self, gTaskNode):
		if gTaskNode.getMItem() == self.__rootMTaskNode:
			self.__resetNetwork()



# ======================================================
class GTaskNode(GRectNode):

	__waitingBgColors = {
		'col' : [240, 240, 240, 255],
		'colSel' : [240, 240, 240, 255],
		}
	__wipBgColors = {
		'col' : [255, 200, 200, 255],
		'colSel' : [255, 200, 200, 255],
		}
	__doneBgColors = {
		'col' : [150, 150, 150, 255],
		'colSel' : [150, 150, 150, 255],
		}

	__style = {
		'bgPaint' : __waitingBgColors,
		}

	_config = DynamicMergeableDict(shapeRoundRadius=1)
	_config.setBase(GRectNode._config)

	def __init__(self, canvas, mTaskNode):
		super(GTaskNode, self).__init__(canvas)

		self._paintStyle = PaintStyle(self.__style, False)
		self._paintStyle.setBaseStyle(GRectNode._paintStyle)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		self.destroyed.connect(self.__onDestroyed)

		self.__mNode = mTaskNode
		mTaskNode.addObserver(self)

		self.__loadUiFile()
		self.__setInitNodeState()
		self.__connectSignalSlot()

		self.__processingAttrNames = set()
		self.__isDescriptionChanging = False

	def getMItem(self):
		return self.__mNode

	def delete(self):
		# To deal with multiple GTaskNode nodes observing the same MTaskNode,
		# we do not delete this UI node directly, instead we delete the model node
		# This GTaskNode instance is deleted when the model node deletion is observed
		self.__mNode.delete()

	def __loadUiFile(self):
		import os, inspect
		dirname = os.path.dirname(inspect.getabsfile(GTaskNode))
		uiFilePath = os.path.join(dirname, 'nodeLook.ui')
		self.__ui = QtCompat.loadUi(uiFilePath)
		self.addWidget(self.__ui)

	def __setInitNodeState(self):
		mTaskNode = self.__mNode
		ui = self.__ui
		self.setPos(*mTaskNode.getAttr('pos'))
		self.resize(*mTaskNode.getAttr('size'))
		ui.estimatedSB.setValue(mTaskNode.getAttr('estimated'))
		ui.actualSB.setValue(mTaskNode.getAttr('actual'))
		ui.descriptionTB.setText(mTaskNode.getAttr('description'))
		ui.descriptionTB.setFocus()
		self.__setActualEnabled()
		self.__setStatus()

	def __connectSignalSlot(self):
		ui = self.__ui
		ui.estimatedSB.valueChanged.connect(self.__onEstimatedChanged)
		ui.actualSB.valueChanged.connect(self.__onActualChanged)
		ui.descriptionTB.textChanged.connect(self.__onDescriptionChanged)

		self.geometryChanged.connect(self.__onGeometryChanged)

	def __setActualEnabled(self):
		hasChild = bool(self.__mNode.getChildren())
		self.__ui.actualSB.setEnabled(not hasChild)
		self.__ui.hasChildL.setVisible(hasChild)

	# Model event callbacks.

	def _onNotify(self, notifier, event, data):
		if event in 'attrChanged':
			# The only node this object is observing is an MTaskNode which this GUI node is for
			self.__onAttrChanged(notifier, data)
		elif event == 'deleted':
			super(GTaskNode, self).delete()
		elif event in ['childAdded', 'childRemoved']:
			self.__setActualEnabled()

	def __onAttrChanged(self, mTaskNode, data):
		attrName, oldValue, newValue = data

		# Avoid potential infinite loop
		# set widget -> qt callback -> MTaskNode callback -> notify event -> set widget ...
		if attrName in self.__processingAttrNames:
			return
		self.__processingAttrNames.add(attrName)

		try:
			if attrName == 'actual':
				self.__ui.actualSB.setValue(newValue)
			elif attrName == 'estimated':
				self.__ui.estimatedSB.setValue(newValue)
			elif attrName == 'description':
				if not self.__isDescriptionChanging:
					self.__ui.descriptionTB.setText(newValue)
			elif attrName == 'pos':
				self.setPos(*newValue)
			elif attrName == 'size':
				self.resize(*newValue)
			elif attrName == 'status':
				self.__setStatus()
		finally:
			self.__processingAttrNames.remove(attrName)

	def __setStatus(self):
		newValue = self.__mNode.getAttr('status')
		if newValue == 'waiting':
			bgColors = self.__waitingBgColors
		elif newValue == 'wip':
			bgColors = self.__wipBgColors
		elif newValue == 'done':
			bgColors = self.__doneBgColors
		self._paintStyle.setBgBrush(bgColors['col'], bgColors['colSel'])

	# Qt GraphicsWidget callbacks

	def __onGeometryChanged(self):
		pos = self.pos()
		size = self.size()
		self.__mNode.setAttr('pos', (pos.x(), pos.y()))
		self.__mNode.setAttr('size', (size.width(), size.height()))

	# Qt widget callbacks

	def __onEstimatedChanged(self, value):
		self.__mNode.setAttr('estimated', value)

	def __onActualChanged(self, value):
		self.__mNode.setAttr('actual', value)

	def __onDescriptionChanged(self):
		text = self.__ui.descriptionTB.toHtml()
		self.__isDescriptionChanging = True
		try:
			self.__mNode.setAttr('description', text)
		finally:
			self.__isDescriptionChanging = False

	def __onDestroyed(self):
		self.__mNode.removeObserver(self)

	def paint(self, painter, option, widget):
		super(GTaskNode, self).paint(painter, option, widget)
		self._paintStyle.applyBorderPen(painter, False)
		self._paintStyle.applyBgBrush(painter, False)
		painter.drawText(self.boundingRect(), self.getMItem().getName())

# ------------------------------------------------------
class GTaskDotNode(GDotNode):

	__style = {
		'bgPaint' : {
			'col' : [150, 150, 150, 255],
			'colSel' : [150, 150, 150, 255],
			}
		}

	_paintStyle = PaintStyle(__style, False)
	_paintStyle.setBaseStyle(GDotNode._paintStyle)

	def __init__(self, canvas, mTaskDotNode):
		super(GTaskDotNode, self).__init__(canvas)
		self.__mNode = mTaskDotNode
		mTaskDotNode.addObserver(self)
		self.__isPosChanging = False
		self.geometryChanged.connect(self.__onGeometryChanged)
		self.setPos(*mTaskDotNode.getAttr('pos'))

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		self.destroyed.connect(self.__onDestroyed)

	def getMItem(self):
		return self.__mNode

	def delete(self):
		self.__mNode.delete()

	# Model event callbacks.

	def _onNotify(self, notifier, event, data):

		if event in 'attrChanged' and data[0] == 'pos':
			if not self.__isPosChanging:
				self.__isPosChanging = True
				try:
					self.setPos(*self.__mNode.getAttr('pos'))
				finally:
					self.__isPosChanging = False

		elif event == 'deleted':
			super(GTaskDotNode, self).delete()

	# Qt GraphicsWidget callbacks

	def __onGeometryChanged(self):
		pos = self.pos()
		self.__mNode.setAttr('pos', (pos.x(), pos.y()))

	def __onDestroyed(self):
		self.__mNode.removeObserver(self)

# ------------------------------------------------------
class GTaskConnection(GConnection):

	def __init__(self, canvas, mConnection):
		"""
		This node assumes the canvas can show the mConnection
		If not creating the instance doesn't show the connection
		You can check it before creating an instance by
			GTaskConnection.canCanvasShowConnection(canvas, mConnection)
		or if you have created an instance
			gConnection.isValid()
		"""
		gNodeFrom = self.__findGNode(mConnection.getFrom(), canvas)
		gNodeTo = self.__findGNode(mConnection.getTo(), canvas)
		if not(gNodeFrom and gNodeTo):
			self.__mNode = None
			return

		super(GTaskConnection, self).__init__(gNodeFrom, gNodeTo)
		self.__mNode = mConnection
		mConnection.addObserver(self)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		self.destroyed.connect(self.__onDestroyed)

	def isValid(self):
		return bool(self.__mNode)

	def getMItem(self):
		return self.__mNode

	def delete(self):
		self.__mNode.delete()

	@staticmethod
	def canCanvasShowConnection(self, canvas, mConnection):
		# Test if both ends of the connection are displayed on the canvas
		gNodeFrom = self.__findGNode(mConnection.getFrom(), canvas)
		gNodeTo = self.__findGNode(mConnection.getTo(), canvas)
		return gNodeFrom and gNodeTo

	@staticmethod
	def __findGNode(mNode, canvas):
		for gNode in canvas.items():
			if hasattr(gNode, 'getMItem') and gNode.getMItem() == mNode: # hasattr() mmm...
				return gNode

	# Model event callbacks.

	def _onNotify(self, notifier, event, data):
		if event == 'deleted':
			super(GTaskConnection, self).delete()

	# Qt event callbacks.

	def __onDestroyed(self):
		self.__mNode.removeObserver(self)

# ======================================================
if __name__ == '__main__':
	import sys
	from Qt import QtWidgets
	from taskModel import MTaskModel, MTaskConnection

	global app
	app = QtWidgets.QApplication(sys.argv)
	model = MTaskModel()
	canvas = GTaskCanvas(model)
	canvas.show()
	app.exec_()

# ======================================================
# if __name__ == '__main__':

# 	from taskModel import MTaskNode, MTaskDotNode, MTaskConnection

# 	def createNetwork():
# 		root = MTaskNode()
# 		pt1 = MTaskNode(root)
# 		pt2 = MTaskNode(root)
# 		ct1 = MTaskNode(pt1)
# 		ct2 = MTaskNode(pt1)
# 		gt1 = MTaskNode(ct2)
# 		cd1 = MTaskDotNode(ct1)
# 		c1 = MTaskConnection(ct1, ct2)

# 		pt1.setAttr('pos', (0, 60))
# 		pt2.setAttr('pos', (170, 60))
# 		ct1.setAttr('pos', (0, 120))
# 		ct2.setAttr('pos', (170, 120))
# 		gt1.setAttr('pos', (170, 180))

# 		ct1.setAttr('actual', 3.0)
# 		gt1.setAttr('actual', 4.0)


# 		from utils.treeNode import serialize
# 		return serialize([root, pt1, pt2, ct1, ct2, gt1, cd1, c1])

# 	global app

# 	import sys
# 	app = QtWidgets.QApplication(sys.argv)

# 	from nodeViewFramework.frameworkMain import GCanvas
# 	canvas = GCanvas()
# 	canvas2 = GCanvas()

# 	pickledNetwork = createNetwork()
# 	import cPickle as pickle
# 	network1 = pickle.loads(pickledNetwork)
# 	network2 = pickle.loads(pickledNetwork)

# 	def getGClass(item):
# 		return {
# 			MTaskNode : GTaskNode,
# 			MTaskDotNode : GTaskDotNode,
# 			MTaskConnection : GTaskConnection,
# 			}[item.__class__]

# 	for item in network1:
# 		gClass = getGClass(item)
# 		gClass(canvas, item)
# 		gClass(canvas2, item)
# 	for item in network2:
# 		gClass = getGClass(item)
# 		gt = gClass(canvas, item)
# 		if item.isNode():
# 			pos = item.getAttr('pos')
# 			item.setAttr('pos', (pos[0] + 360, pos[1] + 10))

# 	canvas.show()
# 	canvas2.show()

# 	app.exec_()
