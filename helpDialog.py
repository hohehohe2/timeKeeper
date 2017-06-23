import os
import inspect
from Qt import QtWidgets, QtCompat

class HelpDialog(QtWidgets.QWidget):
	def __init__(self):
		super(HelpDialog, self).__init__()
		dirname = os.path.dirname(inspect.getabsfile(HelpDialog))
		uiFilePath = os.path.join(dirname, 'help.ui')
		self.__ui = QtCompat.loadUi(uiFilePath, self)

	def keyPressEvent(self, event):
		super(HelpDialog, self).keyPressEvent(event)
		self.close()
