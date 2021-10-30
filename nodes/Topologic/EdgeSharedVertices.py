import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvEdgeSharedVertices(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the vertices shared by the input edges
	"""
	bl_idname = 'SvEdgeSharedVertices'
	bl_label = 'Edge.SharedVertices'
	Edge1: StringProperty(name="Edge1", update=updateNode)
	Edge2: StringProperty(name="Edge2", update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Edge A')
		self.inputs.new('SvStringsSocket', 'Edge B')
		self.outputs.new('SvStringsSocket', 'Vertices')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs1 = self.inputs[0].sv_get(deepcopy=False)[0]
		inputs2 = self.inputs[1].sv_get(deepcopy=False)[0]
		outputs = []
		for i in range(len(inputs1)):
			input1 = inputs1[i]
			input2 = inputs2[i]
			vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
			_ = topologic.Edge.SharedVertices(input1, input2, vertices)
			for aVertex in vertices:
				outputs.append(aVertex)
		self.outputs['Vertices'].sv_set([outputs])

def register():
	bpy.utils.register_class(SvEdgeSharedVertices)

def unregister():
	bpy.utils.unregister_class(SvEdgeSharedVertices)
