GScene, GView, GNodeBase, GRectNode, GDotNode, GConnection

- Purely GUI components for node network
- No sense of hierarchy
- For general purpose

		QtWidgets.QGraphicsScene
			GScene:	Scene to show node networks

		QtWidgets.QGraphicsView
			GView: View to show node networks

		QtWidgets.QGraphicsWidget
			GConnection: Connection widget

		QtWidgets.QGraphicsWidget
			GNodeBase: Base class of nodes to show node networks
				GRectNode: Rectanguler node, can have arbitrary QWidgets inside
				GDotNode: Dot node

# ------------------------------------------------------
MNode

- Model components, no sense of GUI
- Has attribute
- Has hierarchy
- Event notification mechanism
- Supports pickling
- For general purpose

		MNode: Base class of a model nodes that support attribute, event notification, grouping

# ------------------------------------------------------
GNodeSceneBase

- A class incharge of creating and registering GNode (ie. for GUI) from MNode network
- To use this class, GNode subclass constructors must be compatible with this node
- For general purpose

		GScene
			GNodeSceneBase: GScene to be used with MNode classes

# ======================================================
MTaskNode, MTaskDotNode

- Model nodes for time keeper application

		MNode
			MTaskNode: Regular task model node
			MTaskDotNode: Dot model node

# ------------------------------------------------------
GTaskNode, GTaskDotNode

- Gui nodes for time keeper application (though GTaskDotNode can be used for any application)
- These are compatible with GNodeSceneBase requirement

		GRectNode
			GTaskNode: Regular task GUI node
		GDotNode
			GTaskDotNode: Dot task GUI node

# ------------------------------------------------------
GTaskNodeScene

- GNodeScene for timekeeper application
- Offers MNode subclass -> GNode subclass mapping

		GNodeSceneBase
			GTaskNodeScene: Concreate GNodeScene class for timekeeper application
