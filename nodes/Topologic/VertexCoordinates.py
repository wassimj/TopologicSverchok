import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

class SvVertexCoordinates(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the coordinates of the input Vertex    
	"""
	bl_idname = 'SvVertexCoordinates'
	bl_label = 'Vertex.Coordinates'
	Vertex: StringProperty(name="Vertex", update=updateNode)
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.outputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.outputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.outputs.new('SvStringsSocket', 'Z').prop_name = 'Z'

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertices = self.inputs[0].sv_get(deepcopy=False)[0]
		xCoords = []
		yCoords = []
		zCoords = []
		for aVertex in vertices:
			xCoords.append(aVertex.X())
			yCoords.append(aVertex.Y())
			zCoords.append(aVertex.Z())
	
		self.outputs['X'].sv_set([xCoords])
		self.outputs['Y'].sv_set([yCoords])
		self.outputs['Z'].sv_set([zCoords])

def register():
	bpy.utils.register_class(SvVertexCoordinates)

def unregister():
	bpy.utils.unregister_class(SvVertexCoordinates)
