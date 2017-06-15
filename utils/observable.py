# ======================================================
class Observable(object):

	def __init__(self):
		self.__observers = []

	def addObserver(self, observer):
		if observer not in self.__observers:
			self.__observers.append(observer)

	def removeObserver(self, observer):
		if observer in self.__observers:
			self.__observers.remove(observer)

	def clearObservers(self):
			self.__observers = []

	def getObservers(self):
		return self.__observers

	def _notify(self, event, data=None):
		for observer in self.__observers:
			observer._onNotify(self, event, data)

	def _onNotify(self, notifier, event, data):
		pass
