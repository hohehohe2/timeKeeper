import os
import inspect
import datetime
from utils.gitStorage import GitStorage
from Qt import QtCore, QtGui, QtWidgets, QtCompat

class GitNavigator(QtWidgets.QWidget):

	__hexShaColumn = 0
	__dateColumn = 1
	__messageColumn = 2

	def __init__(self, mTaskModel):
		super(GitNavigator, self).__init__()

		repoPath = os.environ['TIME_KEEPER_GIT_REPOSITORY']
		self.__creatRepoIfNotExists(repoPath)
		self.__gitStorage = GitStorage(repoPath, 'data.tkpickle')

		self.__mTaskModel = mTaskModel
		self.__loadUiFile()
		self.__connectSignalSlot()
		self.updateUi()
		self.__load()

	def __creatRepoIfNotExists(self, repoPath):
		if not GitStorage.isRepoReady(repoPath):
			dirname = os.path.dirname(inspect.getabsfile(GitNavigator))
			initRepoTemplateDir = os.path.join(dirname, 'initRepo')
			os.system('cp -r %s %s' % (initRepoTemplateDir, repoPath))

	def __loadUiFile(self):
		dirname = os.path.dirname(inspect.getabsfile(GitNavigator))
		uiFilePath = os.path.join(dirname, 'loadDialog.ui')
		self.__ui = QtCompat.loadUi(uiFilePath, self)

	def __connectSignalSlot(self):
		ui = self.__ui
		ui.scrabHS.valueChanged.connect(self.__onScrabValueChanged)
		ui.logTW.itemClicked.connect(self.__onLogItemClicked)
		ui.logTW.itemSelectionChanged.connect(self.__onLogItemSelectionChanged)
		ui.savePB.clicked.connect(self.__onSave)

	def updateUi(self):
		logs = self.__log()
		logs.reverse()

		maxLogCount = len(logs) - 1

		scrabHS = self.__ui.scrabHS
		scrabHS.setMaximum(maxLogCount)
		scrabHS.setValue(maxLogCount)

		logTW = self.__ui.logTW
		logTW.hideColumn(self.__hexShaColumn)
		logTW.setRowCount(len(logs))

		for rowCount, log in enumerate(logs):
			message, hexSha, date = log
			dateStr = datetime.datetime.fromtimestamp(date).strftime('%Y/%m/%d %H:%M:%S')

			logTW.setItem(rowCount, self.__hexShaColumn, QtWidgets.QTableWidgetItem(hexSha))
			logTW.setItem(rowCount, self.__dateColumn, QtWidgets.QTableWidgetItem(dateStr))
			logTW.setItem(rowCount, self.__messageColumn, QtWidgets.QTableWidgetItem(message.replace('\n', ' ')))

		logTW.selectRow(maxLogCount)

	def __save(self, commitMessage):
		dumpString = self.__mTaskModel.getDumpString()
		self.__gitStorage.save(dumpString, commitMessage)

	def __load(self):
		row = self.__ui.logTW.currentRow()
		item = self.__ui.logTW.item(row, self.__hexShaColumn)
		if item:
			hexSha = item.text()
			dumpString = self.__gitStorage.load(hexSha)
			self.__mTaskModel.setDumpString(dumpString)

	def __log(self, maxCount=-1): # [(message, hexSha, date)]
		return self.__gitStorage.log(maxCount)

	def __onScrabValueChanged(self, value):
		self.__ui.logTW.selectRow(value)

	def __onLogItemClicked(self, items):
		row = self.__ui.logTW.currentRow()
		self.__ui.scrabHS.setValue(row)

	def __onLogItemSelectionChanged(self):
		row = self.__ui.logTW.currentRow()
		self.__ui.scrabHS.setValue(row)
		self.__load()

	def __onSave(self):

		commitMessage, isOk = QtWidgets.QInputDialog.getText(
			None,
			'Save&Commit',
			"Message:", QtWidgets.QLineEdit.Normal,
			'')

		if isOk:
			self.__save(commitMessage)
			self.updateUi()

	def _onNotify(self, notifier, event, data):
		if event == 'toggleGitNavigator':
			self.__toggleVisibility()

	def keyPressEvent(self, event):
		super(GitNavigator, self).keyPressEvent(event)

		if event.modifiers() == QtCore.Qt.ControlModifier:
			if event.key() == QtCore.Qt.Key_G:
				self.__toggleVisibility()

	def __toggleVisibility(self):
		isVisible = self.isVisible()
		self.setVisible(not isVisible)
