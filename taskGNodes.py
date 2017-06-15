# Timekeeper GUI node

from Qt import QtGui, QtWidgets, QtCompat
from nodeViewFramework.gnode_main import GRectNode, GDotNode, GConnection
from nodeViewFramework.paintStyle import PaintStyle
from nodeViewFramework.mergeableDict import DynamicMergeableDict

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

		self.__mTaskNode = mTaskNode
		mTaskNode.addObserver(self)

		self.__loadUiFile()
		self.__setInitNodeState()
		self.__connectSignalSlot()

		self.__processingAttrNames = set()
		self.__isDescriptionChanging = False

	def delete(self):
		# To deal with multiple GTaskNode nodes observing the same MTaskNode,
		# we do not delete this UI node directly, instead we delete the model node
		# This GTaskNode instance is deleted when the model node deletion is observed
		self.__mTaskNode.delete()

	def __loadUiFile(self):
		import os, inspect
		dirname = os.path.dirname(inspect.getabsfile(GTaskNode))
		uiFilePath = os.path.join(dirname, 'nodeLook.ui')
		self.__ui = QtCompat.loadUi(uiFilePath)
		self.addWidget(self.__ui)

	def __setInitNodeState(self):
		mTaskNode = self.__mTaskNode
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
		hasChild = bool(self.__mTaskNode.getChildren())
		self.__ui.actualSB.setEnabled(not hasChild)

	# MTreeNode event callbacks.

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
		self.__mTaskNode.setAttr('pos', (pos.x(), pos.y()))
		self.__mTaskNode.setAttr('size', (size.width(), size.height()))

	# Qt widget callbacks

	def __onEstimatedChanged(self, value):
		self.__mTaskNode.setAttr('estimated', value)

	def __onActualChanged(self, value):
		self.__mTaskNode.setAttr('actual', value)

	def __onDescriptionChanged(self):
		text = self.__ui.descriptionTB.toHtml()
		self.__isDescriptionChanging = True
		try:
			self.__mTaskNode.setAttr('description', text)
		finally:
			self.__isDescriptionChanging = False

# ------------------------------------------------------
class GTaskDotNode(GDotNode):

	def __init__(self, canvas, mTaskDotNode):
		super(GTaskDotNode, self).__init__(canvas)
		self.__mTaskDotNode = mTaskDotNode
		mTaskDotNode.addObserver(self)
		self.__isPosChanging = False

	def delete(self):
		self.__mTaskDotNode.delete()

	# MTreeNode event callbacks.

	def _onNotify(self, notifier, event, data):

		if event in 'attrChanged' and data[0] == 'pos':
			if not self.__isPosChanging:
				self.__isPosChanging = True
				try:
					self.setPos(*mTaskNode.getAttr('pos'))
				finally:
					self.__isPosChanging = False

		elif event == 'deleted':
			super(GTaskDotNode, self).delete()

	# Qt GraphicsWidget callbacks

	def __onGeometryChanged(self):
		pos = self.pos()
		self.__mTaskDotNode.setAttr('pos', (pos.x(), pos.y()))

# ------------------------------------------------------
class GTaskConnection(GConnection):

	def __init__(self, canvas, mConnection):
		super(GTaskConnection, self).__init__(mConnection.getFrom(), mConnection.getTo())
		self.__mConnection = mConnection

	def delete(self):
		self.__mConnection.delete()

# ======================================================
if __name__ == '__main__':

	def createNetwork():
		from taskModel import MTaskNode
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

		from taskModel import serialize
		return serialize([root, pt1, pt2, ct1, ct2, gt1])

	global app

	import sys
	app = QtWidgets.QApplication(sys.argv)

	from nodeViewFramework.gnode_main import GCanvas
	canvas = GCanvas()

	pickledNetwork = createNetwork()
	import cPickle as pickle
	network1 = pickle.loads(pickledNetwork)
	network2 = pickle.loads(pickledNetwork)

	for node in network1:
		GTaskNode(canvas, node)
	for node in network2:
		gt = GTaskNode(canvas, node)
		pos = node.getAttr('pos')
		node.setAttr('pos', (pos[0] + 360, pos[1] + 10))

	canvas.show()
	app.exec_()
