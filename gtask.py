# Timekeeper GUI node

from Qt import QtGui, QtWidgets, QtCompat
from gnode.gnode_main import GRectNode, GDotNode
from gnode.gnode_utils import PaintStyle
from nody_utils.mergeableDict import DynamicMergeableDict

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

	def __init__(self, scene, mTaskNode):
		super(GTaskNode, self).__init__(scene)

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

	def getMTaskNode(self):
		"""
		Get the MTaskNode this object is for
		"""
		return self.__mTaskNode

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

	def __onMTaskNodeDeleted(self):
		super(GTaskNode, self).delete()

	# MNode event callbacks.

	def _onNotify(self, notifier, event, data):
		if event in 'attrChanged':
			# The only node this object is observing is an MTaskNode which this GUI node is for
			self.__onAttrChanged(notifier, data)
		elif event == 'deleted':
			self.__onMTaskNodeDeleted()
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

	def __setActualEnabled(self):
		hasChild = bool(self.__mTaskNode.getChildren())
		self.__ui.actualSB.setEnabled(not hasChild)

	# Qt graphicsWidget callbacks

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

	def __init__(self, scene, mDotNode):
		super(GTaskDotNode, self).__init__(scene)
		self.__mDotNode = mDotNode
		mDotNode.addObserver(self)
		self.__isPosChanging = False

	# MNode event callback.

	def _onNotify(self, notifier, event, data):

		if event in 'attrChanged' and data[0] == 'pos':

			if self.__isPosChanging:
				return
			self.__isPosChanging = True

			try:
				self.setPos(*mTaskNode.getAttr('pos'))
			finally:
				self.__isPosChanging = False

	# Qt graphicsWidget callbacks

	def __onGeometryChanged(self):
		pos = self.pos()
		self.__mTaskNode.setAttr('pos', (pos.x(), pos.y()))

# ======================================================
if __name__ == '__main__':

	def createNetwork():
		from mtask import MTaskNode
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

		from mnode.mnode_main import serialize
		return serialize([root, pt1, pt2, ct1, ct2, gt1])

	global app, view

	import sys
	app = QtWidgets.QApplication(sys.argv)

	from gnode.gnode_main import GScene, GView
	scene = GScene()
	view = GView(None, scene)

	pickledNetwork = createNetwork()
	import cPickle as pickle
	network1 = pickle.loads(pickledNetwork)
	network2 = pickle.loads(pickledNetwork)

	for node in network1:
		GTaskNode(scene, node)
	for node in network2:
		gt = GTaskNode(scene, node)
		pos = node.getAttr('pos')
		node.setAttr('pos', (pos[0] + 360, pos[1] + 10))

	view.show()
	app.exec_()
