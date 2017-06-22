import sys
from Qt import QtWidgets
from taskModel import MTaskModel
from taskView import GTaskCanvas
from gitNavigator import GitNavigator
app = QtWidgets.QApplication(sys.argv)

model = MTaskModel()

canvas = GTaskCanvas(model)
canvas.show()

loadDialog = GitNavigator(model)
loadDialog.show()

app.exec_()
