import copy
import Qt
from Qt import QtGui, QtCore, QtWidgets
from mergeableDict import MergeableDict

# ======================================================
# Default style values used by PaintStyle class
_defaultStyle = {
	'borderPen' : {
		'col' : [50, 50, 50, 255],
		'colSel' : [255, 0, 0, 255],
		'size' : 1,
		'sizeSel' : 3,
		},
	'bgPaint' : {
		'col' : [200, 255, 255, 255],
		'colSel' : [200, 255, 255, 255],
		},
	}

# ------------------------------------------------------
class PaintStyle(object):

	def __init__(self, config=None):
		self.__styleInfo = MergeableDict()
		self.update(_defaultStyle)		

	def update(self, config):
		"""
		Update the style with the given config.
		Style values can be updated partially. Values that are not overriden stay the same.
		"""
		s = self.__styleInfo
		s.update(copy.deepcopy(config))

		self.setBorderPen(s['borderPen']['col'], s['borderPen']['colSel'], s['borderPen']['size'], s['borderPen']['sizeSel'])
		self.setBgBrush(s['bgPaint']['col'], s['bgPaint']['colSel'])
		self.setBorderBrush(s['borderPen']['col'], s['borderPen']['colSel'])

	def setBorderPen(self, borderPenCol, borderPenColSel, borderPenSize, borderPenSizeSel):
		self.__borderPen = PaintStyle.__createPen(QtCore.Qt.SolidLine, borderPenSize, borderPenCol)
		self.__borderPenSel = PaintStyle.__createPen(QtCore.Qt.SolidLine, borderPenSizeSel, borderPenColSel)

	def setBgBrush(self, bgPaintCol, bgPaintColSel):
		self.__bgBrush = self.__createBrush(bgPaintCol)
		self.__bgBrushSel = self.__createBrush(bgPaintColSel)

	def setBorderBrush(self, paintCol, paintColSel):
		self.__borderBrush = self.__createBrush(paintCol)
		self.__borderBrushSel = self.__createBrush(paintColSel)

	def applyBorderPen(self, painter, isSelected):
		if isSelected:
			painter.setPen(self.__borderPenSel)
		else:
			painter.setPen(self.__borderPen)

	def applyBgBrush(self, painter, isSelected):
		if isSelected:
			painter.setBrush(self.__bgBrushSel)
		else:
			painter.setBrush(self.__bgBrush)

	def applyBorderBrush(self, painter, isSelected):
		if isSelected:
			painter.setBrush(self.__borderBrushSel)
		else:
			painter.setBrush(self.__borderBrush)

	@staticmethod
	def __createPen(lineStyle, width, color):
		pen = QtGui.QPen()
		pen.setStyle(lineStyle)
		pen.setWidth(width)
		pen.setColor(QtGui.QColor(*color))
		return pen

	@staticmethod
	def __createBrush(color):
		brush = QtGui.QBrush(QtGui.QColor(*color))
		brush.setStyle(QtCore.Qt.SolidPattern)
		return brush

# ------------------------------------------------------
class ConfigMixin(object):
	"""
	Subclass must have _paintStyle and _config members.
	"""
	@classmethod
	def updateStyle(cls, scene, config=None, paintConfig=None):
		"""
		Update the paint style with config. Can be updated partially
		"""
		if paintConfig:
			cls._paintStyle.update(paintConfig)
		if config:
			cls._config.merge(config)

		scene.update()

# ------------------------------------------------------
def getLineTanNormal(line):
	unitLine = line.unitVector()
	normalLine = unitLine.normalVector()

	tangentVector = unitLine.p2() - unitLine.p1()
	normalVector = normalLine.p2() - normalLine.p1()

	return tangentVector, normalVector

# ======================================================
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

	_config = MergeableDict()
	_paintStyle = PaintStyle()

	def __init__(self, scene):
		super(GNodeBase, self).__init__()
		scene.addItem(self)

		self.__connections = []

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
		self.setZValue(scene.getMaxZValue() + 1)

	def delete(self):
		"""
		Delete this node, and all the connections from/to this node
		"""
		while self.__connections:
			connection = self.__connections.pop()
			connection.delete()
		self.scene().removeItem(self)

	def _getCenter(self):
		"""
		Returns the center of the node. Subclasses must provide an implementation
		"""
		raise NotImplementedError

	def _getIntersectPoint(self, line):
		"""
		Returns the point where the line hits this node. Subclasses must provide an implementation
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
			self.setZValue(self.scene().getMaxZValue() + 1)
		return super(GNodeBase, self).itemChange(change, value)

# ------------------------------------------------------
class GConnection(QtWidgets.QGraphicsObject, ConfigMixin):

	_paintStyle = PaintStyle()
	_config = MergeableDict(
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
		# TODO: Fix the problem where a node is visible and the connection from/to the node is not
		self.setZValue(-1.0E5)

		self.update()

	def delete(self):
		"""
		Deletes this connection
		"""
		self.__nodeFrom._removeConnection(self)
		self.__nodeTo._removeConnection(self)
		self.scene().removeItem(self)
		self.__nodeFrom = None
		self.__nodeTo = None

	def __getArrowHeadPolygon(self):
		line = QtCore.QLineF(self.__nodeFrom._getCenter(), self.__nodeTo._getCenter())
		arrowTip = self.__nodeTo._getIntersectPoint(line)
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

		centerF = self.__nodeFrom._getCenter()
		centerT = self.__nodeTo._getCenter()

		line = QtCore.QLineF(centerF, centerT)
		tangentVector, normalVector = getLineTanNormal(line)

		linePolygon = QtGui.QPolygonF()
		linePolygon.append(centerF - normalVector * linewidth)
		linePolygon.append(centerF + normalVector * linewidth)
		linePolygon.append(centerT + normalVector * linewidth)
		linePolygon.append(centerT - normalVector * linewidth)

		path.addPolygon(linePolygon)

		return path

	def boundingRect(self):
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

		painter.drawLine(self.__nodeFrom._getCenter(), self.__nodeTo._getCenter())
		arrowHead = self.__getArrowHeadPolygon()
		if arrowHead:
			self._paintStyle.applyBorderBrush(painter, isSelected)
			painter.drawPolygon(arrowHead);

# ======================================================
class GRectNode(GNodeBase):

	_config = copy.deepcopy(GNodeBase._config)
	_config.merge({
		'shapeRoundRadius' : 3,
		'dragBorderWidth' : 4,
		'minSize' : [20, 20],
		'widgetLayoutType' : 'vertical', # 'horizontal', 'vertical', or 'none'
		'widgetlayoutSpacing' : 1,
		})

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

	def _getIntersectPoint(self, line):
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

		wlType = self._config['widgetLayoutType']
		if wlType == 'horizontal':
			isDraggableX = False
		elif wlType == 'vertical':
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

	_config = copy.deepcopy(GNodeBase._config)
	_config.merge({
		'dotRadius' : 10,
		})

	def __init__(self, scene, x, y):
		super(GDotNode, self).__init__(scene)
		self.setPos(x - self.__radius(), y - self.__radius())

	def _getCenter(self):
		return self.mapToScene(QtCore.QPointF(self.__radius(), self.__radius()))

	def _getIntersectPoint(self, line):
		center = self._getCenter()
		tangentVector, normalVector = getLineTanNormal(line)
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

	c5.delete()
	n3.delete() # Deletes c2 and c3 too

	# pb is deleted automatically when n1 is deleted
	def cb(*args):print 'widget destroyed'
	pb.destroyed.connect(cb)
	#n1.delete();
	n1 = None # If Python keeps a reference to the widget it won't be destroyed

	view.show()

	app.exec_()

