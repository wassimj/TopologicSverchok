import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvVertexX(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the X coordinate of the input Vertex    
	"""
	bl_idname = 'SvVertexX'
	bl_label = 'Vertex.X'
	X: FloatProperty(name="X", default=0, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.outputs.new('SvStringsSocket', 'X').prop_name = 'X'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertices = self.inputs[0].sv_get(deepcopy=False)[0]
		xCoords = []
		for aVertex in vertices:
			xCoords.append(aVertex.X())
	
		self.outputs['X'].sv_set([xCoords])

def register():
	bpy.utils.register_class(SvVertexX)

def unregister():
	bpy.utils.unregister_class(SvVertexX)
