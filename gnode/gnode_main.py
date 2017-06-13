# Simple node UI framework.
# A node can have arbitrary Qt widgets inside.
# There is no concept of grouping, ie. nested nodes through parent-child relationship
#
# Some of the code in this file are taken from nodz (https://github.com/LeGoffLoic/Nodz)
# Copywright of the parts are held by LeGoffLoic

import copy
from Qt import QtGui, QtCore, QtWidgets
from nody_utils.mergeableDict import DynamicMergeableDict
from gnode_utils import PaintStyle, ConfigMixin, getLineTanNormal

# ======================================================
# nody main classes

class GScene(QtWidgets.QGraphicsScene):

	def keyPressEvent(self, event):
		super(GScene, self).keyPressEvent(event)

		if event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
			while self.selectedItems():
				self.selectedItems()[0].delete()

		self.update()

	def getMaxZValue(self):
		maxValue = 0
		for item in self.items():
			if item.zValue() > maxValue:
				maxValue = item.zValue()
		return maxValue

# ------------------------------------------------------
class GView(QtWidgets.QGraphicsView):

	def __init__(self, parent, scene):
		super(GView, self).__init__(parent)
		self.setScene(scene)

		self.setRenderHint(QtGui.QPainter.Antialiasing, True)
		self.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
		self.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)
		self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
		self.setRenderHint(QtGui.QPainter.NonCosmeticDefaultPen, True)
		self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

# ------------------------------------------------------
class GNodeBase(QtWidgets.QGraphicsWidget, ConfigMixin):

	def __init__(self, scene):
		super(GNodeBase, self).__init__()
		scene.addItem(self)

		self.__connections = []

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
		self.setZValue(scene.getMaxZValue() + 1)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

	def delete(self):
		"""
		Delete this node, and all the connections from/to this node
		"""
		while self.__connections:
			connection = self.__connections.pop()
			connection.delete()
		self.close()

	def _getCenter(self):
		"""
		Returns the center of the node. Subclasses must provide an implementation
		"""
		raise NotImplementedError

	def _getIntersectPoint(self, line, isStart):
		"""
		Returns the point where the line hits this node. Subclasses must provide an implementation
		If isStart is True, the line start point is assumed to be inside the node and it should return
		the point where the line is going out of the node shape.

		If isStart is False, the line end point is assumed to be inside the node and it should return
		the point where the line is going into the node shape.
		"""
		raise NotImplementedError

	def _addConnection(self, connection):
		if not connection in self.__connections:
			self.__connections.append(connection)

	def _removeConnection(self, connection):
		if connection in self.__connections:
			self.__connections.remove(connection)

	# Qt callbacks

	def boundingRect(self):
		"""
		Subclasses must provide an implementation
		"""
		raise NotImplementedError

	def paint(self, painter, option, widget):
		"""
		Subclasses must provide an implementation
		"""
		raise NotImplementedError

	def mouseMoveEvent(self, event):
		super(GNodeBase, self).mouseMoveEvent(event)
		for connection in self.__connections:
			connection.update()

	def itemChange(self, change, value):
		if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
			newMaxZValue = self.scene().getMaxZValue() + 1
			self.setZValue(newMaxZValue)
			for connection in self.__connections:
				connection.setZValue(newMaxZValue)

		return super(GNodeBase, self).itemChange(change, value)

# ------------------------------------------------------
class GConnection(QtWidgets.QGraphicsWidget, ConfigMixin):

	_paintStyle = PaintStyle()
	_config = DynamicMergeableDict(
		arrowHeadSize = 5,
		selectionLineWidth = 4,
		)

	def __init__(self, nodeFrom, nodeTo):
		super(GConnection, self).__init__()

		scene = nodeFrom.scene()
		assert(scene == nodeTo.scene())
		scene.addItem(self)

		nodeFrom._addConnection(self)
		nodeTo._addConnection(self)

		self.__nodeFrom = nodeFrom
		self.__nodeTo = nodeTo

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
		# TODO: Fix the problem where a node is occluded by another node and the connection from/to the node is not
		self.setZValue(scene.getMaxZValue() + 1)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

	def delete(self):
		"""
		Deletes this connection
		"""
		self.__nodeFrom._removeConnection(self)
		self.__nodeTo._removeConnection(self)
		self.close()
		self.__nodeFrom = None
		self.__nodeTo = None

	def __getArrowHeadPolygon(self):
		line = QtCore.QLineF(self.__nodeFrom._getCenter(), self.__nodeTo._getCenter())
		arrowTip = self.__nodeTo._getIntersectPoint(line, False)
		if not arrowTip:
			return

		tangentVector, normalVector = getLineTanNormal(line)

		arrowHeadSize = self._config['arrowHeadSize']
		baseCenter = arrowTip - tangentVector * arrowHeadSize * 2
		baseCorner1 = baseCenter - normalVector * arrowHeadSize
		baseCorner2 = baseCenter + normalVector * arrowHeadSize

		arrowHead = QtGui.QPolygonF()
		arrowHead.append(arrowTip)
		arrowHead.append(baseCorner1)
		arrowHead.append(baseCorner2)

		return arrowHead

	# Qt callbacks

	def shape(self):
		path = QtGui.QPainterPath()
		arrowHead = self.__getArrowHeadPolygon()
		if arrowHead:
			path.addPolygon(arrowHead)

		# Make the line thicker for easy selection

		linewidth = self._config['selectionLineWidth']

		line = QtCore.QLineF(self.__nodeFrom._getCenter(), self.__nodeTo._getCenter())
		arrowTip = self.__nodeTo._getIntersectPoint(line, False)
		arrowTail = self.__nodeFrom._getIntersectPoint(line, True)
		if (not arrowTip) or (not arrowTail):
			return path

		tangentVector, normalVector = getLineTanNormal(line)

		linePolygon = QtGui.QPolygonF()
		linePolygon.append(arrowTail - normalVector * linewidth)
		linePolygon.append(arrowTail + normalVector * linewidth)
		linePolygon.append(arrowTip + normalVector * linewidth)
		linePolygon.append(arrowTip - normalVector * linewidth)

		path.addPolygon(linePolygon)

		return path

	def boundingRect(self):

		# boundingRect() is called after self.close() inside delete() and before the node is actually deleted
		# Disable boundingRect() code execution if it has been deleted().
		# __nodeFrom is None if and only if delete() has been called
		if not self.__nodeFrom:
			return QtCore.QRectF()

		rect = QtCore.QRectF(self.__nodeFrom._getCenter(), self.__nodeTo._getCenter())

		arrowHead = self.__getArrowHeadPolygon()

		if arrowHead:
			return rect.united(arrowHead.boundingRect())
		else:
			return rect

	def paint(self, painter, option, widget):
		isSelected = self.isSelected()
		self._paintStyle.applyBorderPen(painter, isSelected)
		self._paintStyle.applyBgBrush(painter, isSelected)

		line = QtCore.QLineF(self.__nodeFrom._getCenter(), self.__nodeTo._getCenter())
		arrowTip = self.__nodeTo._getIntersectPoint(line, False)
		arrowTail = self.__nodeFrom._getIntersectPoint(line, True)
		if (not arrowTip) or (not arrowTail):
			return

		painter.drawLine(arrowTail, arrowTip)
		arrowHead = self.__getArrowHeadPolygon()
		if arrowHead:
			self._paintStyle.applyBorderBrush(painter, isSelected)
			painter.drawPolygon(arrowHead);

# ======================================================
# Concrete node classes

class GRectNode(GNodeBase):

	_paintStyle = PaintStyle()
	_config = DynamicMergeableDict(
		shapeRoundRadius=3,
		dragBorderWidth=4,
		dragCursorEnabled=(True, True), # horizontal, vertical
		minSize=[20, 20],
		widgetLayoutType='vertical', # 'horizontal', 'vertical', or 'none'
		widgetlayoutSpacing=1,
		margins = (3, 8, 3, 3) # left, top, right, bottom
		)

	def __init__(self, scene, x, y, width, height):
		super(GRectNode, self).__init__(scene)

		self.setPos(x, y)
		self.__setWidthHeight(width, height)
		self.setAcceptHoverEvents(True)
		self.__setLayout()

	def addWidget(self, widget):
		proxy = QtWidgets.QGraphicsProxyWidget(parent=self)
		proxy.setWidget(widget)
		if self.layout():
			self.layout().addItem(proxy)

	def _getCenter(self):
		return self.mapToScene(QtCore.QPointF(self.size().width() / 2.0, self.size().height() / 2.0))

	def _getIntersectPoint(self, line, isStart):
		polygon = self.mapToScene(self.boundingRect())
		p1 = polygon.first()
		for i in range(1, polygon.count()):
			p2 = polygon.at(i)
			polyLine = QtCore.QLineF(p1, p2)
			intersectType, intersectPoint = polyLine.intersect(line)
			if intersectType == QtCore.QLineF.BoundedIntersection:
				return intersectPoint;
			p1 = p2;

	def __isDraggable(self, event):
		pos = event.pos()
		bRect = self.boundingRect()
		dragBorderWidth = self._config['dragBorderWidth']

		isDraggableX = bRect.right() - pos.x() < dragBorderWidth
		isDraggableY = bRect.bottom() - pos.y() < dragBorderWidth

		return isDraggableX, isDraggableY

	def __setDraggableCursor(self, isDraggableX, isDraggableY):

		horizontal, vertical = self._config['dragCursorEnabled']
		if not horizontal:
			isDraggableX = False
		if not vertical:
			isDraggableY = False

		if isDraggableX and isDraggableY:
			self.setCursor(QtCore.Qt.SizeFDiagCursor)
		elif isDraggableX:
			self.setCursor(QtCore.Qt.SizeHorCursor)
		elif isDraggableY:
			self.setCursor(QtCore.Qt.SizeVerCursor)
		else:
			self.setCursor(QtCore.Qt.ArrowCursor)

	def __setWidthHeight(self, width, height):
		minSizeX, minSizeY = self._config['minSize']
		self.resize(width, height)

	def __setLayout(self):
		wlType = self._config['widgetLayoutType']
		layout = None
		if wlType == 'horizontal':
			layout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Horizontal)
			self.setLayout(layout)
			layout.setSpacing(1)
		elif wlType == 'vertical':
			layout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Vertical)
			self.setLayout(layout)

		if layout:
			layout.setSpacing(self._config['widgetlayoutSpacing'])
			layout.setContentsMargins(3, 8, 3, 3)

	# Qt callbacks

	def boundingRect(self):
		return QtCore.QRectF(0, 0, self.size().width(), self.size().height())

	def paint(self, painter, option, widget):
		isSelected = self.isSelected()
		self._paintStyle.applyBorderPen(painter, isSelected)
		self._paintStyle.applyBgBrush(painter, isSelected)
		r = self._config['shapeRoundRadius']
		painter.drawRoundedRect(self.boundingRect(), r, r)

	def mousePressEvent(self, event):
		super(GRectNode, self).mousePressEvent(event)

		self.__doDragX, self.__doDragY = self.__isDraggable(event)

		if self.__doDragX or self.__doDragY:
			self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)

		self.__setDraggableCursor(self.__doDragX, self.__doDragY)

	def mouseMoveEvent(self, event):
		super(GRectNode, self).mouseMoveEvent(event)

		if self.__doDragX or self.__doDragY:
			dragAmount = event.pos() - event.lastPos()

			if self.__doDragX:
				self.__setWidthHeight(self.size().width() + dragAmount.x(), self.size().height())
			if self.__doDragY:
				self.__setWidthHeight(self.size().width(), self.size().height() + dragAmount.y())

			self.update()

	def mouseReleaseEvent(self, event):
		super(GRectNode, self).mouseReleaseEvent(event)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
		self.setCursor(QtCore.Qt.ArrowCursor)

	def hoverEnterEvent(self, event):
		super(GRectNode, self).hoverEnterEvent(event)
		self.__setDraggableCursor(*self.__isDraggable(event))

	def hoverMoveEvent(self, event):
		super(GRectNode, self).hoverMoveEvent(event)
		self.__setDraggableCursor(*self.__isDraggable(event))

	def hoverLeaveEvent(self, event):
		super(GRectNode, self).hoverLeaveEvent(event)
		self.setCursor(QtCore.Qt.ArrowCursor)

# ------------------------------------------------------
class GDotNode(GNodeBase):

	_paintStyle = PaintStyle()
	_config = DynamicMergeableDict(
		dotRadius=10,
		)

	def __init__(self, scene, x, y):
		super(GDotNode, self).__init__(scene)
		self.setPos(x - self.__radius(), y - self.__radius())

	def _getCenter(self):
		return self.mapToScene(QtCore.QPointF(self.__radius(), self.__radius()))

	def _getIntersectPoint(self, line, isStart):
		center = self._getCenter()
		tangentVector, normalVector = getLineTanNormal(line)
		if isStart:
			return center + tangentVector * self.__radius()
		else:
			return center - tangentVector * self.__radius()

	def __radius(self):
		return self._config['dotRadius']

	# Qt callbacks

	def boundingRect(self):
		return QtCore.QRectF(0, 0, self.__radius() * 2, self.__radius() * 2)

	def paint(self, painter, option, widget):
		isSelected = self.isSelected()
		self._paintStyle.applyBorderPen(painter, isSelected)
		self._paintStyle.applyBgBrush(painter, isSelected)
		painter.drawEllipse(self.boundingRect())

# ======================================================
if __name__ == '__main__':
	global app, view

	import sys
	app = QtWidgets.QApplication(sys.argv)

	scene = GScene()
	view = GView(None, scene)

	config = {'shapeRoundRadius':4}
	GRectNode.updateStyle(scene, config)

	n1 = GRectNode(scene, 30, 30, 100, 100)
	n2 = GDotNode(scene, 150, 150)
	n3 = GRectNode(scene, 200, 30, 15, 50)
	n4 = GRectNode(scene, 200, 130, 50, 15)
	c1 = GConnection(n1, n2)
	c2 = GConnection(n3, n4)
	c3 = GConnection(n2, n3)
	c4 = GConnection(n2, n4)
	c5 = GConnection(n4, n1)

	pb = QtWidgets.QPushButton()
	n1.addWidget(pb)
	n1.addWidget(QtWidgets.QLineEdit())

	def cb1(*args):print 'connection c5 destroyed'
	c5.destroyed.connect(cb1)
	c5.delete() # You can manually delete the connection in the UI by selecting it and hit delete key
	def cb2(*args):print 'connection c2 destroyed'
	c2.destroyed.connect(cb2)
	n3.delete() # Deletes c2 and c3 too

	# Widgets inside a node are deleted automatically when the node is deleted
	def cb3(*args):print 'node n1 destroyed'
	n1.destroyed.connect(cb3)
	def cb4(*args):print 'button widget destroyed'
	pb.destroyed.connect(cb4)
	#n1.delete(); # You can manually delete the node in the UI by selecting it and hit delete key

	view.show()

	app.exec_()

