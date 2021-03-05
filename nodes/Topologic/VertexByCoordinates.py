import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic

class SvVertexByCoordinates(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Vertex from the input coordinates   
	"""
	bl_idname = 'SvVertexByCoordinates'
	bl_label = 'Vertex.ByCoordinates'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	lacing: EnumProperty(name='Lacing', items=list_match_modes, default='REPEAT', update=updateNode)

	def sv_init(self, context):
		#self.inputs[0].label = 'Auto'
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.outputs.new('SvStringsSocket', 'Vertex')

	def draw_buttons_ext(self, context, layout):
		layout.separator()
		layout.label(text="Lacing:")
		layout.prop(self, 'lacing', expand=False)

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		xCoords = self.inputs['X'].sv_get(deepcopy=False)[0]
		yCoords = self.inputs['Y'].sv_get(deepcopy=False)[0]
		zCoords = self.inputs['Z'].sv_get(deepcopy=False)[0]
		maxLength = max([len(xCoords), len(yCoords), len(zCoords)])
		for i in range(len(xCoords), maxLength):
			xCoords.append(xCoords[-1])
		for i in range(len(yCoords), maxLength):
			yCoords.append(yCoords[-1])
		for i in range(len(zCoords), maxLength):
			zCoords.append(zCoords[-1])
		coords = []
		if (len(xCoords) == len(yCoords) == len(zCoords)):
			coords = zip(xCoords, yCoords, zCoords)
			vertices = []
			for coord in coords:
				try:
					vertices.append(topologic.Vertex.ByCoordinates(coord[0], coord[1], coord[2]))
				except:
					continue
			self.outputs['Vertex'].sv_set([vertices])

def register():
    bpy.utils.register_class(SvVertexByCoordinates)

def unregister():
    bpy.utils.unregister_class(SvVertexByCoordinates)
