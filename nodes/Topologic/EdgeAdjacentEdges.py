import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
class SvEdgeAdjacentEdges(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Edges connected to the input Edge
	"""
	bl_idname = 'SvEdgeAdjacentEdges'
	bl_label = 'Edge.AdjacentEdges'
	Edge: StringProperty(name="Edge", update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge')
		self.outputs.new('SvStringsSocket', 'Edges').prop_name = 'Edges'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs[0].sv_get(deepcopy=False)[0]
		outputs = []
		for anInput in inputs:
			edges = cppyy.gbl.std.list[topologic.Edge.Ptr]()
			_ = anInput.AdjacentEdges(edges)
			for anEdge in edges:
				outputs.append(anEdge)
		self.outputs['Edges'].sv_set([outputs])

def register():
	bpy.utils.register_class(SvEdgeAdjacentEdges)

def unregister():
	bpy.utils.unregister_class(SvEdgeAdjacentEdges)
