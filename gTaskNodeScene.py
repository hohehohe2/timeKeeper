from mgscene.gNodeScene import GNodeSceneBase
from mtask import MTaskNode, MTaskDotNode
from gtask import GTaskNode, GTaskDotNode

# ======================================================
class GTaskNodeScene(GNodeSceneBase):
	_classMapper = {
		MTaskNode : GTaskNode,
		MTaskDotNode : GTaskDotNode,
		}


# ======================================================
if __name__ == '__main__':
	import sys
	from Qt import QtWidgets
	from gnode.gnode_main import GView

	def createNetwork():

		root = MTaskNode()
		pt1 = MTaskNode(root)
		pt2 = MTaskNode(root)
		ct1 = MTaskNode(pt1)
		ct2 = MTaskNode(pt1)
		gt1 = MTaskNode(ct2)

		pt1.setAttr('pos', (0, 60))
		pt2.setAttr('pos', (170, 60))
		ct1.setAttr('pos', (0, 120))
		ct2.setAttr('pos', (170, 120))
		gt1.setAttr('pos', (170, 180))

		ct1.setAttr('actual', 3.0)
		gt1.setAttr('actual', 4.0)

		from mnode.mnode_main import serialize
		return serialize([root, pt1, pt2, ct1, ct2, gt1])

	global app, view

	app = QtWidgets.QApplication(sys.argv)

	scene = GTaskNodeScene()
	view = GView(None, scene)

	pickledNetwork = createNetwork()
	import cPickle as pickle
	root, pt1, pt2, ct1, ct2, gt1 = pickle.loads(pickledNetwork)

	scene.resetNetwork(root, ())

	ct1.setParent(root)
	ct2.setParent(root)
	scene.addNetwork([ct1, ct2], ())

	view.show()
	app.exec_()
