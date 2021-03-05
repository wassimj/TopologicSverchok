import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvVertexZ(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the Z coordinate of the input Vertex    
	"""
	bl_idname = 'SvVertexZ'
	bl_label = 'Vertex.Z'
	Z: FloatProperty(name="Z", default=0, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.outputs.new('SvStringsSocket', 'Z').prop_name = 'Z'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertices = self.inputs[0].sv_get(deepcopy=False)[0]
		zCoords = []
		for aVertex in vertices:
			zCoords.append(aVertex.Z())
	
		self.outputs['Z'].sv_set([zCoords])

def register():
	bpy.utils.register_class(SvVertexZ)

def unregister():
	bpy.utils.unregister_class(SvVertexZ)
