from Qt import QtGui, QtWidgets, QtCompat
from gnode.gnode_main import GScene, GView, GRectNode
from gnode.gnode_utils import PaintStyle
from mtask import MTask

# ======================================================
# Prefix 'G' means 'GUI'
class GTask(GRectNode):

	def __init__(self, scene, mTask):
		super(GTask, self).__init__(scene, 0, 0, 0, 0)

		base = self._paintStyle
		self._paintStyle = PaintStyle()
		self._paintStyle.setBaseStyle(base)

		self.__mTask = mTask
		self.__mTask.addObserver(self)

		self.__loadUiFile()
		self.__setInitNodeState()
		self.__connectSignalSlot()

		self.__processingAttrNames = set()
		self.__isDescriptionChanging = False

	def delete(self):
		# To deal with multiple GTask nodes observing the same MTask node,
		# we do not delete this UI node directly, instead we delete the model node
		# This GTask instance is deleted when the model node deletion is observed
		self.__mTask.delete()

	def onNotify(self, notifier, event, data):
		if event in 'attrChanged':
			# This only node this object is observing is MTask that this GUI node is for
			self.__onAttrChanged(notifier, data)
		elif event == 'deleted':
			self.__onMTaskDeleted()
		elif event in ['childAdded', 'childRemoved']:
			self.__setActualEnabled()

	def __loadUiFile(self):
		import os, inspect
		dirname = os.path.dirname(inspect.getabsfile(GTask))
		uiFilePath = os.path.join(dirname, 'nodeLook.ui')
		self.__ui = QtCompat.loadUi(uiFilePath)
		self.addWidget(self.__ui)

	def __setInitNodeState(self):
		mTask = self.__mTask
		ui = self.__ui
		self.setPos(*mTask.getAttr('pos'))
		self.resize(*mTask.getAttr('size'))
		ui.estimatedSB.setValue(mTask.getAttr('estimated'))
		ui.actualSB.setValue(mTask.getAttr('actual'))
		ui.descriptionTB.setText(mTask.getAttr('description'))
		self.__setActualEnabled()

	def __connectSignalSlot(self):
		ui = self.__ui
		ui.estimatedSB.valueChanged.connect(self.__onEstimatedChanged)
		ui.actualSB.valueChanged.connect(self.__onActualChanged)
		ui.descriptionTB.textChanged.connect(self.__onDescriptionChanged)

		self.geometryChanged.connect(self.__onGeometryChanged)

	def __onMTaskDeleted(self):
		super(GTask, self).delete()

	# MTask event callbacks.

	def __onAttrChanged(self, mTask, data):
		attrName, oldValue, newValue = data

		# Avoid potential infinite loop
		# set widget -> qt callback -> MTask callback -> notify event -> set widget ...
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
		hasChild = bool(self.__mTask.getChildren())
		self.__ui.actualSB.setEnabled(not hasChild)

	# Qt graphicsWidget callbacks

	def __onGeometryChanged(self):
		pos = self.pos()
		size = self.size()
		self.__mTask.setAttr('pos', (pos.x(), pos.y()))
		self.__mTask.setAttr('size', (size.width(), size.height()))

	# Qt widget callbacks

	def __onEstimatedChanged(self, value):
		self.__mTask.setAttr('estimated', value)

	def __onActualChanged(self, value):
		self.__mTask.setAttr('actual', value)

	def __onDescriptionChanged(self):
		text = self.__ui.descriptionTB.toHtml()
		self.__isDescriptionChanging = True
		try:
			self.__mTask.setAttr('description', text)
		finally:
			self.__isDescriptionChanging = False

# ======================================================
if __name__ == '__main__':
	root = MTask()
	pt1 = MTask(root, 'pt1')
	pt2 = MTask(root,'pt2')
	ct1 = MTask(pt1, 'ct1')
	ct2 = MTask(pt1, 'ct2')
	gt1 = MTask(ct2, 'gt1')

	pt1.setAttr('pos', (0, 200))
	pt2.setAttr('pos', (300, 200))
	ct1.setAttr('pos', (0, 400))
	ct2.setAttr('pos', (300, 400))
	gt1.setAttr('pos', (300, 600))

	ct1.setAttr('actual', 3.0)
	gt1.setAttr('actual', 4.0)

	global app, view

	import sys
	app = QtWidgets.QApplication(sys.argv)

	scene = GScene()
	view = GView(None, scene)

	rootN = GTask(scene, root)
	pt1N = GTask(scene, pt1)
	pt2N = GTask(scene, pt2)
	ct1N = GTask(scene, ct1)
	ct2N = GTask(scene, ct2)
	gt1N = GTask(scene, gt1)

	view.show()
	app.exec_()
