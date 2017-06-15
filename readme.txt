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
MTreeNode

- Model components, no sense of GUI
- Has attribute
- Has hierarchy
- Event notification mechanism
- Supports pickling
- For general purpose

		object(Python)
			MTreeNode: Base class of a model nodes with attribute, event notification, grouping

# ======================================================
MTaskNode, MTaskDotNode

- Model nodes for time keeper application (though MTaskDotNode can be used for any application)

		MTreeNode
			MTaskNode: Regular task model node for time keeper 
			MTaskDotNode: Dot model node for time keeper

# ------------------------------------------------------
GTaskNode, GTaskDotNode

- Gui nodes for time keeper application (though GTaskDotNode can be used for any application)

		GRectNode
			GTaskNode: Regular task GUI node
		GDotNode
			GTaskDotNode: Dot task GUI node

# ------------------------------------------------------
GTaskTreeNodeCanvas

- Offers MTreeNode subclass -> GNode subclass mapping

		GCanvas
			GTaskTreeNodeCanvas: GCanvas for timekeeper application
