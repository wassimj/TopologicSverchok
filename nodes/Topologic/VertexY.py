import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvVertexY(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Y coordinate of the input Vertex    
	"""
	bl_idname = 'SvVertexY'
	bl_label = 'Vertex.Y'
	Y: FloatProperty(name="Y", default=0, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.outputs.new('SvStringsSocket', 'Y').prop_name = 'Y'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertices = self.inputs[0].sv_get(deepcopy=False)[0]
		yCoords = []
		for aVertex in vertices:
			yCoords.append(aVertex.Y())
	
		self.outputs['Y'].sv_set([yCoords])

def register():
	bpy.utils.register_class(SvVertexY)

def unregister():
	bpy.utils.unregister_class(SvVertexY)
