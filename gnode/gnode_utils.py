# Some of the code in this file are taken from nodz (https://github.com/LeGoffLoic/Nodz)
# Copywright of the parts are held by LeGoffLoic

import copy
from Qt import QtGui, QtCore
from nody_utils.mergeableDict import MergeableDict

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

# ======================================================
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

# ======================================================
def getLineTanNormal(line):
	if line.length() < 1.0E-2:
		return QtCore.QPointF(1.0, 0.0), QtCore.QPointF(0.0, 1.0)

	unitLine = line.unitVector()
	normalLine = unitLine.normalVector()

	tangentVector = unitLine.p2() - unitLine.p1()
	normalVector = normalLine.p2() - normalLine.p1()

	return tangentVector, normalVector
