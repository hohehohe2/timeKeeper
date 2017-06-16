# Timekeeper GUI node

from Qt import QtGui, QtWidgets, QtCompat
from nodeViewFramework.frameworkMain import GRectNode, GDotNode, GConnection
from nodeViewFramework.paintStyle import PaintStyle
from utils.mergeableDict import DynamicMergeableDict


# ======================================================
class GTaskNode(GRectNode):

	style = {
	'bgPaint' : {
		'col' : [240, 240, 240, 255],
		'colSel' : [240, 240, 240, 255],
		}
	}

	_paintStyle = PaintStyle(style, False)
	_paintStyle.setBaseStyle(GRectNode._paintStyle)

	_config = DynamicMergeableDict(shapeRoundRadius=1)
	_config.setBase(GRectNode._config)

	def __init__(self, canvas, mTaskNode):
		super(GTaskNode, self).__init__(canvas)

		self.__mNode = mTaskNode
		mTaskNode.addObserver(self)

		self.__loadUiFile()
		self.__setInitNodeState()
		self.__connectSignalSlot()

		self.__processingAttrNames = set()
		self.__isDescriptionChanging = False

	def getMNode(self):
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
		self.__setActualEnabled()

	def __connectSignalSlot(self):
		ui = self.__ui
		ui.estimatedSB.valueChanged.connect(self.__onEstimatedChanged)
		ui.actualSB.valueChanged.connect(self.__onActualChanged)
		ui.descriptionTB.textChanged.connect(self.__onDescriptionChanged)

		self.geometryChanged.connect(self.__onGeometryChanged)

	def __setActualEnabled(self):
		hasChild = bool(self.__mNode.getChildren())
		self.__ui.actualSB.setEnabled(not hasChild)

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
		finally:
			self.__processingAttrNames.remove(attrName)

		self.update()

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

# ------------------------------------------------------
class GTaskDotNode(GDotNode):

	def __init__(self, canvas, mTaskDotNode):
		super(GTaskDotNode, self).__init__(canvas)
		self.__mNode = mTaskDotNode
		mTaskDotNode.addObserver(self)
		self.__isPosChanging = False
		self.geometryChanged.connect(self.__onGeometryChanged)

	def getMNode(self):
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

	def isValid(self):
		return bool(self.__mNode)

	def getMNode(self):
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
			if hasattr(gNode, 'getMNode') and gNode.getMNode() == mNode: # hasattr() mmm...
				return gNode

	# Model event callbacks.

	def _onNotify(self, notifier, event, data):
		if event == 'deleted':
			super(GTaskConnection, self).delete()

# ======================================================
if __name__ == '__main__':

	from taskModel import MTaskNode, MTaskDotNode, MTaskConnection

	def createNetwork():
		root = MTaskNode()
		pt1 = MTaskNode(root)
		pt2 = MTaskNode(root)
		ct1 = MTaskNode(pt1)
		ct2 = MTaskNode(pt1)
		gt1 = MTaskNode(ct2)
		cd1 = MTaskDotNode(ct1)
		c1 = MTaskConnection(ct1, ct2)

		pt1.setAttr('pos', (0, 60))
		pt2.setAttr('pos', (170, 60))
		ct1.setAttr('pos', (0, 120))
		ct2.setAttr('pos', (170, 120))
		gt1.setAttr('pos', (170, 180))

		ct1.setAttr('actual', 3.0)
		gt1.setAttr('actual', 4.0)


		from utils.treeNode import serialize
		return serialize([root, pt1, pt2, ct1, ct2, gt1, cd1, c1])

	global app

	import sys
	app = QtWidgets.QApplication(sys.argv)

	from nodeViewFramework.frameworkMain import GCanvas
	canvas = GCanvas()
	canvas2 = GCanvas()

	pickledNetwork = createNetwork()
	import cPickle as pickle
	network1 = pickle.loads(pickledNetwork)
	network2 = pickle.loads(pickledNetwork)

	def getGClass(item):
		return {
			MTaskNode : GTaskNode,
			MTaskDotNode : GTaskDotNode,
			MTaskConnection : GTaskConnection,
			}[item.__class__]

	for item in network1:
		gClass = getGClass(item)
		gClass(canvas, item)
		gClass(canvas2, item)
	for item in network2:
		gClass = getGClass(item)
		gt = gClass(canvas, item)
		if item.isNode():
			pos = item.getAttr('pos')
			item.setAttr('pos', (pos[0] + 360, pos[1] + 10))

	canvas.show()
	canvas2.show()

	app.exec_()
