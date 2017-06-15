# Some of the code in this file are taken from nodz (https://github.com/LeGoffLoic/Nodz)
# Copywright of the parts are held by LeGoffLoic

import copy
from Qt import QtGui, QtCore
from mergeableDict import DynamicMergeableDict

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

	def __init__(self, style=_defaultStyle, doUpdate=True):
		self.__styleInfo = DynamicMergeableDict()
		self.__styleInfo.update(style)
		if doUpdate:
			self.__update()

	def setBaseStyle(self, baseConfig):
		self.__styleInfo.setBase(baseConfig.__styleInfo)
		self.__update()

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

	def __update(self):
		s = self.__styleInfo
		self.setBorderPen(s['borderPen']['col'], s['borderPen']['colSel'], s['borderPen']['size'], s['borderPen']['sizeSel'])
		self.setBgBrush(s['bgPaint']['col'], s['bgPaint']['colSel'])
		self.setBorderBrush(s['borderPen']['col'], s['borderPen']['colSel'])

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
class PaintConfigMixin(object):
	"""
	Subclass must have _paintStyle and _config members.
	"""
	@classmethod
	def updateStyle(cls, canvas, config=None, paintConfig=None):
		"""
		Update the paint style with config. Can be updated partially
		"""
		if paintConfig:
			current = cls._paintStyle
			cls._paintStyle = PaintStyle(paintConfig)
			cls._paintStyle.setBaseStyle(current)
		if config:
			current = cls._config
			cls._config = DynamicMergeableDict()
			cls._config.update(config)
			cls._config.setBase(current)

		canvas.update()
