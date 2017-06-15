GCanvas, GNodeBase, GRectNode, GDotNode, GConnection

- Purely GUI components for node network
- No sense of hierarchy
- For general purpose
- Unlike Qt design intention, GCanvas is used only for UI drawing, model is Qt independent
  (QtWidgets.QGraphicsScene is used as a view class in model-view! )

		QtWidgets.QGraphicsScene
			GCanvas:	Scene(canvas) to show node networks

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
GNodeCanvasBase

- A class incharge of creating and registering GNode (ie. for GUI) from MNode network
- Every MNode that a canvas is displaying has the same parent
- Subclass should provide MNode subclass -> GNode subclass mapping
- GNode subclass constructors must be compatible with this node
- For general purpose

		GCanvas
			GNodeCanvasBase: GCanvas to be used with MNode classes

# ======================================================
MTaskNode, MTaskDotNode

- Model nodes for time keeper application

		MNode
			MTaskNode: Regular task model node
			MTaskDotNode: Dot model node

# ------------------------------------------------------
GTaskNode, GTaskDotNode

- Gui nodes for time keeper application (though GTaskDotNode can be used for any application)
- These are compatible with GNodeCanvasBase requirement

		GRectNode
			GTaskNode: Regular task GUI node
		GDotNode
			GTaskDotNode: Dot task GUI node

# ------------------------------------------------------
GTaskNodeCanvas

- GNodeCanvasBase for timekeeper application
- Offers MNode subclass -> GNode subclass mapping

		GNodeCanvasBase
			GTaskNodeCanvas: Concreate GNodeCanvasBase class for timekeeper application
