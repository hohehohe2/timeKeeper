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
TreeNode

- Model components, no sense of GUI
- Has attribute
- Has hierarchy
- Event notification mechanism
- Supports pickling
- For general purpose

		Observable
			TreeNode: Base class of a model nodes with attribute, event notification, grouping

# ======================================================
MTaskNode, MTaskDotNode, MTaskConnection, MTaskModel

- Model nodes for time keeper application

		TreeNode
			MTaskNode: Regular task model node for time keeper 
			MTaskDotNode: Dot model node for time keeper
		Observable
			MTaskConnection: Connection model item for time keeper
		Observable
			MTaskModel: The whole model, observes created mItems to remove from self

# ------------------------------------------------------
GTaskNode, GTaskDotNode, GTaskConnection, GTaskCanvas

- Gui nodes for time keeper application
- GTasKCanvas creates GNode subclasses from TreeNode subclasses

		GRectNode
			GTaskNode: Regular task GUI node
		GDotNode
			GTaskDotNode: Dot task GUI node
		GConnection
			GTaskConnection: Connection task GUI item
		GCanvas, Observable
			GTaskCanvas: GCanvas for timekeeper, observes MTaskModel to know item creation
