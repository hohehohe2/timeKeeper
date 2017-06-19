# Simple node UI framework.
# A node can have arbitrary Qt widgets inside.
# There is no concept of grouping, ie. nested nodes through parent-child relationship
#
# Some of the code in this file are taken from nodz (https://github.com/LeGoffLoic/Nodz)
# Copywright of the parts are held by LeGoffLoic

import copy
from Qt import QtGui, QtCore, QtWidgets
from utils.mergeableDict import DynamicMergeableDict
from paintStyle import PaintStyle, PaintConfigMixin


# ======================================================
def _getLineTanNormal(line):
	if line.length() < 1.0E-2:
		return QtCore.QPointF(1.0, 0.0), QtCore.QPointF(0.0, 1.0)

	unitLine = line.unitVector()
	normalLine = unitLine.normalVector()

	tangentVector = unitLine.p2() - unitLine.p1()
	normalVector = normalLine.p2() - normalLine.p1()

	return tangentVector, normalVector

# ------------------------------------------------------
class _GArrowShapeBase(QtWidgets.QGraphicsWidget, PaintConfigMixin):

	_paintStyle = PaintStyle()
	_config = DynamicMergeableDict(
		arrowHeadSize = 5,
		selectionLineWidth = 4,
		)

	def __init__(self, canvas):
		super(_GArrowShapeBase, self).__init__()

		canvas.addItem(self)

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
		# TODO: Fix the problem where a node is occluded by another node and the connection from/to the node is not
		self.setZValue(canvas.getMaxZValue() + 1)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		self.__isDeleted = False

	def delete(self):
		"""
		Deletes this connection
		"""
		self.close()
		self.__isDeleted = True

	def __getArrowHeadPolygon(self, arrowTail, arrowTip):
		line = QtCore.QLineF(arrowTail, arrowTip)
		tangentVector, normalVector = _getLineTanNormal(line)

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

	def _shape(self, arrowTail, arrowTip):
		path = QtGui.QPainterPath()
		if (not arrowTip) or (not arrowTail):
			return path

		line = QtCore.QLineF(arrowTail, arrowTip)
		tangentVectorUnused, normalVector = _getLineTanNormal(line)
		linewidth = self._config['selectionLineWidth']

		arrowHead = self.__getArrowHeadPolygon(arrowTail, arrowTip)
		path.addPolygon(arrowHead)

		# Make the line thicker for easy selection

		linePolygon = QtGui.QPolygonF()
		linePolygon.append(arrowTail - normalVector * linewidth)
		linePolygon.append(arrowTail + normalVector * linewidth)
		linePolygon.append(arrowTip + normalVector * linewidth)
		linePolygon.append(arrowTip - normalVector * linewidth)

		path.addPolygon(linePolygon)

		return path

	def _boundingRect(self, arrowTail, arrowTip):
		if (not arrowTip) or (not arrowTail):
			return QtCore.QRectF()

		# boundingRect() is called after self.close() inside delete() and before the node is actually deleted
		# Disable boundingRect() code execution if it has been deleted().
		if self.__isDeleted:
			return QtCore.QRectF()

		rect = QtCore.QRectF(arrowTail, arrowTip)

		arrowHead = self.__getArrowHeadPolygon(arrowTail, arrowTip)
		rect = rect.united(arrowHead.boundingRect())

		return rect

	def _paint(self, painter, option, widget, arrowTail, arrowTip, isSelected):
		if (not arrowTip) or (not arrowTail):
			return

		self._paintStyle.applyBorderPen(painter, isSelected)
		self._paintStyle.applyBgBrush(painter, isSelected)
		painter.drawLine(arrowTail, arrowTip)

		self._paintStyle.applyBorderBrush(painter, isSelected)
		arrowHead = self.__getArrowHeadPolygon(arrowTail, arrowTip)
		painter.drawPolygon(arrowHead);

# ------------------------------------------------------
class _GConnectionCreationShape(_GArrowShapeBase):

	def setArrowTail(self, arrowTail):
		self.__arrowTail = arrowTail

	def setArrowTip(self, arrowTip):
		self.__arrowTip = arrowTip

	# Qt callbacks

	def shape(self):
		return self._shape(self.__arrowTail, self.__arrowTip)

	def boundingRect(self):
		return self._boundingRect(self.__arrowTail, self.__arrowTip)

	def paint(self, painter, option, widget):
		self._paint(painter, option, widget, self.__arrowTail, self.__arrowTip, True)

# ======================================================
# nody main classes

class GCanvas(QtWidgets.QGraphicsScene):

	def __init__(self, *args, **kargs):
		super(GCanvas, self).__init__(*args, **kargs)
		self.__view = _GView(None)
		self.__view.setScene(self)
		self.__gNodeFrom = None
		self.__connectionCreationShape = None

	def show(self):
		self.__view.show()

	def getMaxZValue(self):
		maxValue = 0
		for item in self.items():
			if item.zValue() > maxValue:
				maxValue = item.zValue()
		return maxValue

	def mousePressEvent(self, event):
		if event.button() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier:
			itemFrom = self.itemAt(event.scenePos().toPoint(), QtGui.QTransform())
			if isinstance(itemFrom, GNodeBase):
				self.__gNodeFrom = itemFrom
				self.__connectionCreationShape = _GConnectionCreationShape(self)
				self.__connectionCreationShape.setArrowTail(self.__gNodeFrom._getCenter())
				self.__connectionCreationShape.setArrowTip(self.__gNodeFrom._getCenter())
		else:
			super(GCanvas, self).mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if self.__gNodeFrom:
			self.__showArrow(event)
		else:
			super(GCanvas, self).mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		if not self.__gNodeFrom:
			super(GCanvas, self).mouseReleaseEvent(event)
			return

		gnodeFrom = self.__gNodeFrom
		self.__gNodeFrom = None
		self.__connectionCreationShape.delete()
		self.__connectionCreationShape = None
		self.update()

		if not event.button() == QtCore.Qt.LeftButton:
			return 

		itemTo = self.itemAt(event.scenePos().toPoint(), QtGui.QTransform())
		while itemTo.parent():
			itemTo = itemTo.parent()
		if itemTo and isinstance(itemTo, GNodeBase) and itemTo != gnodeFrom:
			self._createConnection(gnodeFrom, itemTo)

	def _createConnection(self, gNodeFrom, gNodeTo):
		"""
		Reimplement this to create application specific connection
		"""
		# NOTE: It creates a connection even if already exists.
		# NOTE: Applications that use this framework almost always overrides this method
		# NOTE: so let's close our eyes for now.
		GConnection(gNodeFrom, gNodeTo)

	def __showArrow(self, event):
		self.__connectionCreationShape.setArrowTip(event.scenePos())
		self.update()

# ------------------------------------------------------
class _GView(QtWidgets.QGraphicsView):

	def __init__(self, parent):
		super(_GView, self).__init__(parent)

		self.setRenderHint(QtGui.QPainter.Antialiasing, True)
		self.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
		self.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)
		self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
		self.setRenderHint(QtGui.QPainter.NonCosmeticDefaultPen, True)
		self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

# ------------------------------------------------------
class GNodeBase(QtWidgets.QGraphicsWidget, PaintConfigMixin):

	def __init__(self, canvas):
		super(GNodeBase, self).__init__()
		canvas.addItem(self)

		self.__connections = []

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
		self.setZValue(canvas.getMaxZValue() + 1)
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
class GConnection(_GArrowShapeBase):

	def __init__(self, nodeFrom, nodeTo):
		canvas = nodeFrom.scene()
		assert(canvas == nodeTo.scene())

		super(GConnection, self).__init__(canvas)

		nodeFrom._addConnection(self)
		nodeTo._addConnection(self)
		self.__nodeFrom = nodeFrom
		self.__nodeTo = nodeTo

	def delete(self):
		"""
		Deletes this connection
		"""
		self.__nodeFrom._removeConnection(self)
		self.__nodeTo._removeConnection(self)
		super(GConnection, self).delete()
		self.__nodeFrom = None
		self.__nodeTo = None

	# Qt callbacks

	def shape(self):
		arrowTail, arrowTip = self.__getArrowTailTip()
		return self._shape(arrowTail, arrowTip)

	def boundingRect(self):
		# boundingRect() is called after self.close() inside delete() and before the node is actually deleted
		# Disable boundingRect() code execution if it has been deleted().
		# __nodeFrom is None if and only if delete() has been called
		if not self.__nodeFrom:
			return QtCore.QRectF()

		arrowTail, arrowTip = self.__getArrowTailTip()
		return self._boundingRect(arrowTail, arrowTip)

	def paint(self, painter, option, widget):
		arrowTail, arrowTip = self.__getArrowTailTip()
		isSelected = self.isSelected()
		self._paint(painter, option, widget, arrowTail, arrowTip, isSelected)

	def __getArrowTailTip(self):
		line = QtCore.QLineF(self.__nodeFrom._getCenter(), self.__nodeTo._getCenter())
		arrowTail = self.__nodeFrom._getIntersectPoint(line, True)
		arrowTip = self.__nodeTo._getIntersectPoint(line, False)
		return arrowTail, arrowTip

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
		margins = (10, 3, 3, 3) # left, top, right, bottom
		)

	def __init__(self, canvas, x=0, y=0, width=40, height=40):
		super(GRectNode, self).__init__(canvas)

		self.setPos(x, y)
		self.__setWidthHeight(width, height)
		self.setAcceptHoverEvents(True)
		self.__setLayout()
		self.__setDraggableCursor(False, False)

	def addWidget(self, widget):
		# It's so weird that without setParent() proxy's parent is None, and it's garbage collected at some point (not immediately).
		# if we remove parent=self Python crashes.
		proxy = QtWidgets.QGraphicsProxyWidget(parent=self)
		proxy.setParent(self)
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
			self.setCursor(QtCore.Qt.ClosedHandCursor)

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
			layout.setContentsMargins(*self._config['margins'])

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
		self.setCursor(QtCore.Qt.ClosedHandCursor)

	def hoverEnterEvent(self, event):
		super(GRectNode, self).hoverEnterEvent(event)
		self.__setDraggableCursor(*self.__isDraggable(event))

	def hoverMoveEvent(self, event):
		super(GRectNode, self).hoverMoveEvent(event)
		self.__setDraggableCursor(*self.__isDraggable(event))

	def hoverLeaveEvent(self, event):
		super(GRectNode, self).hoverLeaveEvent(event)
		self.setCursor(QtCore.Qt.ClosedHandCursor)

# ------------------------------------------------------
class GDotNode(GNodeBase):

	_paintStyle = PaintStyle()
	_config = DynamicMergeableDict(
		dotRadius=10,
		)

	def __init__(self, canvas, x=0, y=0):
		super(GDotNode, self).__init__(canvas)
		self.setPos(x - self.__radius(), y - self.__radius())

	def _getCenter(self):
		return self.mapToScene(QtCore.QPointF(self.__radius(), self.__radius()))

	def _getIntersectPoint(self, line, isStart):
		center = self._getCenter()
		tangentVector, normalVector = _getLineTanNormal(line)
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
	global app

	import sys
	app = QtWidgets.QApplication(sys.argv)

	canvas = GCanvas()

	config = {'shapeRoundRadius':4}
	GRectNode.updateStyle(canvas, config)

	n1 = GRectNode(canvas, 30, 30, 100, 100)
	n2 = GDotNode(canvas, 150, 150)
	n3 = GRectNode(canvas, 200, 30, 15, 50)
	n4 = GRectNode(canvas, 200, 130, 50, 15)
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

	canvas.show()

	app.exec_()

